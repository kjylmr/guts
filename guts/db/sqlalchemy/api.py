# Copyright (c) 2015 Aptira Pty Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Implementation of SQLAlchemy backend."""


import functools
import re
import sys
import threading
import time
import uuid

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db import options
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log as logging
from oslo_utils import timeutils
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import literal_column

from guts.common import sqlalchemyutils
from guts.db.sqlalchemy import models
from guts import exception
from guts.i18n import _
from guts.i18n import _LW


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

options.set_defaults(CONF, connection='sqlite:///$state_path/guts.sqlite')

_LOCK = threading.Lock()
_FACADE = None


def process_sort_params(sort_keys, sort_dirs, default_keys=None,
                        default_dir='asc'):
    """Process the sort parameters to include default keys.

    Creates a list of sort keys and a list of sort directions. Adds the default
    keys to the end of the list if they are not already included.

    When adding the default keys to the sort keys list, the associated
    direction is:
    1) The first element in the 'sort_dirs' list (if specified), else
    2) 'default_dir' value (Note that 'asc' is the default value since this is
    the default in sqlalchemy.utils.paginate_query)

    :param sort_keys: List of sort keys to include in the processed list
    :param sort_dirs: List of sort directions to include in the processed list
    :param default_keys: List of sort keys that need to be included in the
                         processed list, they are added at the end of the list
                         if not already specified.
    :param default_dir: Sort direction associated with each of the default
                        keys that are not supplied, used when they are added
                        to the processed list
    :returns: list of sort keys, list of sort directions
    :raise exception.InvalidInput: If more sort directions than sort keys
                                   are specified or if an invalid sort
                                   direction is specified
    """
    if default_keys is None:
        default_keys = ['created_at', 'id']
    # Determine direction to use for when adding default keys
    if sort_dirs and len(sort_dirs):
        default_dir_value = sort_dirs[0]
    else:
        default_dir_value = default_dir

    # Create list of keys (do not modify the input list)
    if sort_keys:
        result_keys = list(sort_keys)
    else:
        result_keys = []

    # If a list of directions is not provided, use the default sort direction
    # for all provided keys.
    if sort_dirs:
        result_dirs = []
        # Verify sort direction
        for sort_dir in sort_dirs:
            if sort_dir not in ('asc', 'desc'):
                msg = _("Unknown sort direction, must be 'desc' or 'asc'.")
                raise exception.InvalidInput(reason=msg)
            result_dirs.append(sort_dir)
    else:
        result_dirs = [default_dir_value for _sort_key in result_keys]

    # Ensure that the key and direction length match
    while len(result_dirs) < len(result_keys):
        result_dirs.append(default_dir_value)
    # Unless more direction are specified, which is an error
    if len(result_dirs) > len(result_keys):
        msg = _("Sort direction array size exceeds sort key array size.")
        raise exception.InvalidInput(reason=msg)

    # Ensure defaults are included
    for key in default_keys:
        if key not in result_keys:
            result_keys.append(key)
            result_dirs.append(default_dir_value)

    return result_keys, result_dirs


def _create_facade_lazily():
    global _LOCK
    with _LOCK:
        global _FACADE
        if _FACADE is None:
            _FACADE = db_session.EngineFacade(
                CONF.database.connection,
                **dict(CONF.database)
            )

        return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def dispose_engine():
    get_engine().dispose()

_DEFAULT_QUOTA_NAME = 'default'


def get_backend():
    """The backend is this module itself."""

    return sys.modules[__name__]


def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    if not context:
        LOG.warning(_LW('Use of empty request context is deprecated'),
                    DeprecationWarning)
        raise Exception('die')
    return context.is_admin


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True


def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    if is_user_context(context):
        if not context.project_id:
            raise exception.NotAuthorized()
        elif context.project_id != project_id:
            raise exception.NotAuthorized()


def authorize_user_context(context, user_id):
    """Ensures a request has permission to access the given user."""
    if is_user_context(context):
        if not context.user_id:
            raise exception.NotAuthorized()
        elif context.user_id != user_id:
            raise exception.NotAuthorized()


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)
    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`authorize_project_context` and
    :py:func:`authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """

    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)
    return wrapper


def _retry_on_deadlock(f):
    """Decorator to retry a DB API call if Deadlock was received."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except db_exc.DBDeadlock:
                LOG.warning(_LW("Deadlock detected when running "
                                "'%(func_name)s': Retrying..."),
                            dict(func_name=f.__name__))
                # Retry!
                time.sleep(0.5)
                continue
    functools.update_wrapper(wrapped, f)
    return wrapped


def is_valid_model_filters(model, filters):
    """Return True if filter values exist on the model

    :param model: a Guts model
    :param filters: dictionary of filters
    """
    for key in filters.keys():
        try:
            getattr(model, key)
        except AttributeError:
            LOG.debug("'%s' filter key is not valid.", key)
            return False
    return True


def _generate_paginate_query(context, session, marker, limit, sort_keys,
                             sort_dirs, filters, offset=None,
                             paginate_type=models.Migration):
    """Generate the query to include the filters and the paginate options.

    Returns a query with sorting / pagination criteria added or None
    if the given filters will not yield any results.

    :param context: context to query under
    :param session: the session to use
    :param marker: the last item of the previous page; we returns the next
                    results after this value.
    :param limit: maximum number of items to return
    :param sort_keys: list of attributes by which results should be sorted,
                      paired with corresponding item in sort_dirs
    :param sort_dirs: list of directions in which results should be sorted,
                      paired with corresponding item in sort_keys
    :param filters: dictionary of filters; values that are in lists, tuples,
                    or sets cause an 'IN' operation, while exact matching
                    is used for other values, see _process_volume_filters
                    function for more information
    :param offset: number of items to skip
    :param paginate_type: type of pagination to generate

    :returns: updated query or None
    """
    sort_keys, sort_dirs = process_sort_params(sort_keys,
                                               sort_dirs,
                                               default_dir='desc')
    query = _hypervisor_get_query(context, session=session)

    if filters:
        query = query.filter_by(**filters)
        if query is None:
            return None

    marker_object = None
    if marker is not None:
        marker_object = _hypervisor_get(context, marker, session)

    return sqlalchemyutils.paginate_query(query, paginate_type, limit,
                                          sort_keys,
                                          marker=marker_object,
                                          sort_dirs=sort_dirs,
                                          offset=offset)


def model_query(context, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('project_only')

    query = session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)
    else:
        raise Exception(
            _("Unrecognized read_deleted value '%s'") % read_deleted)

    if project_only and is_user_context(context):
        query = query.filter_by(project_id=context.project_id)

    return query


# Hypervisors

@require_context
def _hypervisor_get_query(context, session=None):
    """Get the query to retrieve the hypervisor.

    :param context: the context used to run the method _hypervisor_get_query
    :param session: the session to use
    :param joined_load: the boolean used to decide whether the query loads
                        the other models, which join the volume model in
                        the database. Currently, the False value for this
                        parameter is specially for the case of updating
                        database during volume migration
    :returns: updated query or None
    """
    return model_query(context, models.Hypervisor, session=session)


@require_context
def hypervisor_get_all(context, filters=None, marker=None,limit=None,
                       offset=None, sort_keys=None, sort_dirs=None):
    """Returns a dict describing all hypervisors"""
    if filters and not is_valid_model_filters(models.Hypervisor, filters):
        return []

    session = get_session()
    with session.begin():
        # Generate the paginate query
        query = _generate_paginate_query(context, session, marker,
                                         limit, sort_keys, sort_dirs, filters,
                                         offset, models.Hypervisor)
        if query is None:
            return []
        return query.all()


@require_context
def hypervisor_get_all_by_host(context, host, inactive=False):
    """Returns a dict describing all hypervisors."""
    read_deleted = "yes" if inactive else "no"
    query = _hypervisor_get_query(context)

    return query.filter_by(host=host).all()

@require_context
def _hypervisor_get(context, hypervisor_id, session=None):
    result = _hypervisor_get_query(
        context, session).\
        filter_by(id=hypervisor_id).\
        first()

    if not result:
        raise exception.hypervisorNotFound(hypervisor=hypervisor_id)

    return result


@require_context
def hypervisor_get(context, hypervisor_id, session=None):
    """Return a dict describing specific hypervisor."""
    return _hypervisor_get(context, hypervisor_id,
                           session)


@require_context
def hypervisor_create(context, values):
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())

    session = get_session()

    with session.begin():
        try:
            hypervisor_ref = models.Hypervisor()
            hypervisor_ref.update(values)
            session.add(hypervisor_ref)
        except Exception as e:
            raise db_exc.DBError(e)

        return hypervisor_ref


@require_admin_context
def hypervisor_delete(context, hypervisor_id):
    session = get_session()
    with session.begin():
        hypervisor = hypervisor_get(context, hypervisor_id,
                                    session)
        if not hypervisor:
            raise exception.HypervisorNotFound(
                hypervisor=hypervisor_id)
        hypervisor.update({'deleted': True,
                           'deleted_at': timeutils.utcnow(),
                           'updated_at': literal_column('updated_at')})


@require_context
def hypervisor_get_all_by_type(context, type, session=None):
    hypervisors = _hypervisor_get_query(
        context, session).\
        filter_by(type=type)
    return hypervisors.all()


@require_context
def hypervisor_get_by_name(context, name, session=None):
    hypervisor = _hypervisor_get_query(
        context, session).\
        filter_by(name=name).\
        first()

    if not hypervisor:
        raise exception.HypervisorNotFound(hypervisor=name)

    return hypervisor

@require_admin_context
def hypervisor_update(context, hypervisor_id, values):
    session = get_session()
    with session.begin():
        hypervisor_ref = _hypervisor_get(context, hypervisor_id, session=session)
        hypervisor_ref.update(values)
        return hypervisor_ref


# Resources

def _resource_get_query(context, session=None, read_deleted=None,
                        expected_fields=None):
    expected_fields = expected_fields or []
    query = model_query(context,
                        models.Resource,
                        session=session,
                        read_deleted=read_deleted)

    if 'projects' in expected_fields:
        query = query.options(joinedload('projects'))

    return query


@require_context
def resource_get_all(context, inactive=False):
    """Returns a dict describing all resources with id as key."""
    read_deleted = "yes" if inactive else "no"
    query = _resource_get_query(context, read_deleted=read_deleted)

    return query.order_by("id").all()


@require_context
def _resource_get(context, resource_id, session=None):
    result = _resource_get_query(
        context, session).\
        filter_by(id=resource_id).\
        first()

    if not result:
        raise exception.ResourceNotFound(resource_id=resource_id)

    return result


@require_context
def resource_get(context, resource_id, session=None):
    """Return a dict describing specific resource."""
    return _resource_get(context, resource_id,
                         session)


@require_context
def resource_create(context, values):
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())

    session = get_session()

    with session.begin():
        try:
            resource_ref = models.Resource()
            resource_ref.update(values)
            session.add(resource_ref)
        except Exception as e:
            raise db_exc.DBError(e)

        return resource_ref


@require_admin_context
def resource_delete(context, resource_id):
    session = get_session()
    with session.begin():
        resource = resource_get(context, resource_id,
                                session)
        if not resource:
            raise exception.ResourceNotFound(
                resource_id=resource_id)
        resource.update({'deleted': True,
                         'deleted_at': timeutils.utcnow(),
                         'updated_at': literal_column('updated_at')})


@require_context
def resource_get_all_by_type(context, resource_type, session=None):
    result = model_query(context, models.Resource, session=session).\
        filter_by(type=resource_type)

    return result


@require_context
def resource_get_by_id_at_source(context, id_at_source, session=None):
    result = _resource_get_query(
        context, session).\
        filter_by(id_at_source=id_at_source).\
        first()

    if not result:
        raise exception.ResourceNotFound(resource_id=id_at_source)

    return result


@require_context
def _resources_get_by_source(context, source, session=None):
    result = model_query(context, models.Resource, session=session).\
        filter_by(source=source)

    return result


@require_admin_context
def resource_delete_all_by_source(context, source):
    session = get_session()
    with session.begin():
        resources = _resources_get_by_source(context, source,
                                             session)

        for resource in resources:
            resource.update({'deleted': True,
                             'deleted_at': timeutils.utcnow(),
                             'updated_at': literal_column('updated_at')})


@require_admin_context
def resource_update(context, resource_id, values):
    session = get_session()
    with session.begin():
        resource_ref = _resource_get(context, resource_id, session=session)
        resource_ref.update(values)
        return resource_ref


# Migrations


def _migration_get_query(context, session=None, read_deleted=None,
                         expected_fields=None):
    expected_fields = expected_fields or []
    query = model_query(context,
                        models.Migration,
                        session=session,
                        read_deleted=read_deleted)

    if 'projects' in expected_fields:
        query = query.options(joinedload('projects'))

    return query


@require_context
def migration_get_all(context, inactive=False):
    read_deleted = "yes" if inactive else "no"
    query = _migration_get_query(context, read_deleted=read_deleted)

    return query.order_by("name").all()


@require_context
def _migration_get(context, id, session=None):
    result = _migration_get_query(
        context, session).\
        filter_by(id=id).\
        first()

    if not result:
        raise exception.MigrationNotFound(migration_id=id)

    return result


@require_context
def migration_get(context, id, session=None):
    return _migration_get(context, id, session)


@require_context
def _migration_get_by_name(context, name, session=None):
    result = model_query(context, models.Migration, session=session).\
        filter_by(name=name).\
        first()

    if not result:
        raise exception.MigrationNotFoundByName(migration_name=name)
    return result


@require_context
def migration_get_by_name(context, name):
    return _migration_get_by_name(context, name)


@require_admin_context
def migration_delete(context, migration_id):
    session = get_session()
    with session.begin():
        migration = migration_get(context, migration_id,
                                  session)
        if not migration:
            raise exception.MigrationNotFound(
                migration_id=migration_id)
        migration.update({'deleted': True,
                          'deleted_at': timeutils.utcnow(),
                          'updated_at': literal_column('updated_at')})


@require_admin_context
def migration_create(context, values, projects=None):
    """Create a new migration."""
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())

    session = get_session()

    with session.begin():
        # Check, if any migration exist with the same ID.
        try:
            _migration_get(context, values['id'], session)
            raise exception.MigrationExists(id=values['id'])
        except exception.MigrationNotFound:
            pass

        try:
            migration_ref = models.Migration()
            migration_ref.update(values)
            session.add(migration_ref)
        except Exception as e:
            raise db_exc.DBError(e)

        return migration_ref


@require_admin_context
def migration_update(context, migration_id, values):
    session = get_session()
    with session.begin():
        migration_ref = _migration_get(context, migration_id, session=session)
        migration_ref.update(values)
        return migration_ref


# Service

@require_admin_context
def service_destroy(context, service_id):
    session = get_session()
    with session.begin():
        service_ref = _service_get(context, service_id, session=session)
        service_ref.delete(session=session)


@require_admin_context
def _service_get(context, service_id, session=None):
    result = model_query(
        context,
        models.Service,
        session=session).\
        filter_by(id=service_id).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)

    return result


@require_admin_context
def service_get(context, service_id):
    return _service_get(context, service_id)


@require_admin_context
def service_get_all(context, disabled=None):
    query = model_query(context, models.Service)

    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    return query.all()


@require_admin_context
def service_get_all_by_topic(context, topic, disabled=None):
    query = model_query(
        context, models.Service, read_deleted="no").\
        filter_by(topic=topic)

    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    return query.all()


@require_admin_context
def service_get_by_host_and_topic(context, host, topic):
    result = model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(host=host).\
        filter_by(topic=topic).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=None)
    return result


@require_admin_context
def service_get_by_args(context, host, binary):
    results = model_query(context, models.Service).\
        filter_by(host=host).\
        filter_by(binary=binary).\
        all()

    for result in results:
        if host == result['host']:
            return result

    raise exception.ServiceNotFound(service_id=binary,
                                    host=host)


@require_admin_context
def service_create(context, values):
    service_ref = models.Service()
    if not values.get('id'):
        values['id'] = str(uuid.uuid4())
    service_ref.update(values)
    if not CONF.enable_new_services:
        service_ref.disabled = True

    session = get_session()
    with session.begin():
        # Check, if any migration exist with the same ID.
        try:
            _service_get(context, values['id'], session)
            raise exception.ServiceExists(id=values['id'])
        except exception.ServiceNotFound:
            pass

        service_ref.save(session)
        return service_ref


@require_admin_context
@_retry_on_deadlock
def service_update(context, service_id, values):
    session = get_session()
    with session.begin():
        service_ref = _service_get(context, service_id, session=session)
        if ('disabled' in values):
            service_ref['modified_at'] = timeutils.utcnow()
            service_ref['updated_at'] = literal_column('updated_at')
        service_ref.update(values)
        return service_ref


# Extra

_GET_METHODS = {}


@require_context
def get_by_id(context, model, id, *args, **kwargs):
    # Add get method to cache dictionary if it's not already there
    if not _GET_METHODS.get(model):
        _GET_METHODS[model] = _get_get_method(model)

    return _GET_METHODS[model](context, id, *args, **kwargs)


def get_model_for_versioned_object(versioned_object):
    # Exceptions to model mapping, in general Versioned Objects have the same
    # name as their ORM models counterparts, but there are some that diverge
    VO_TO_MODEL_EXCEPTIONS = {
    }

    model_name = versioned_object.obj_name()
    return (VO_TO_MODEL_EXCEPTIONS.get(model_name) or
            getattr(models, model_name))


def _get_get_method(model):
    # Exceptions to model to get methods, in general method names are a simple
    # conversion changing ORM name from camel case to snake format and adding
    # _get to the string
    GET_EXCEPTIONS = {
    }

    if model in GET_EXCEPTIONS:
        return GET_EXCEPTIONS[model]

    # General conversion
    # Convert camel cased model name to snake format
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model.__name__)
    # Get method must be snake formatted model name concatenated with _get
    method_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower() + '_get'
    return globals().get(method_name)
