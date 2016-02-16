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

"""The source hypervisors."""

import six
import webob

from oslo_log import log as logging

from guts.api import extensions
from guts.api.openstack import wsgi
from guts.api.views import migrations as views_migrations
from guts import exception
from guts.migration import migrations
from guts import rpc
from guts import utils

LOG = logging.getLogger(__name__)

authorize = extensions.extension_authorizer('migration', 'migrations_manage')


class MigrationsController(wsgi.Controller):
    """The migration API controller for the OpenStack API."""
    _view_builder_class = views_migrations.ViewBuilder

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(MigrationsController, self).__init__()

    def _notify_migration_error(self, ctxt, method, err,
                                migration=None, id=None, name=None):
        payload = dict(migrations=migration, name=name, id=id,
                       error_message=err)
        rpc.get_notifier('migration').error(ctxt, method, payload)

    def _notify_migration_info(self, ctxt, method, migration):
        payload = dict(migrations=migration)
        rpc.get_notifier('migration').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Migrations."""
        context = req.environ['guts.context']
        mgts = migrations.get_all_migrations(context)
        mgts = list(mgts.values())
        req.cache_resource(mgts, name='migrations')
        return self._view_builder.index(req, mgts)

    def show(self, req, id):
        """Returns data about given migration."""
        context = req.environ['guts.context']
        try:
            migration = migrations.get_migration(context, id)
            req.cache_resource(migration, name='migrations')
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        return self._view_builder.show(req, migration)

    def create(self, req, body):
        """Creates a migration process."""
        ctxt = req.environ['guts.context']

        authorize(ctxt)

        migration = body['migration']
        name = migration.get('name', None)
        source_instance_id = migration.get('source_instance_id')
        description = migration.get('description')

        if description is not None:
            utils.check_string_length(description, 'Migration description',
                                      min_length=0, max_length=255)

        try:
            migration = migrations.create(ctxt,
                                          name,
                                          source_instance_id,
                                          description=description)
            req.cache_resource(migration, name='migrations')
            self._notify_migration_info(
                ctxt, 'migration.create', migration)
        except exception.MigrationExists as err:
            self._notify_migration_error(
                ctxt, 'migration.create', err, migration=migration)
            raise webob.exc.HTTPConflict(explanation=six.text_type(err))
        except exception.MigrationNotFoundByName as err:
            self._notify_migration_error(
                ctxt, 'migration_.create', err, name=name)
            raise webob.exc.HTTPNotFound(explanation=err.msg)

        return self._view_builder.show(req, migration)

    def delete(self, req, id):
        """Returns the list of Migrations."""
        context = req.environ['guts.context']
        authorize(context)

        # TODO(Bharat): Enable this later.
        # if self._source_in_use(context, type_id):
        #    expl = _('Cannot delete source type. Source type in use.')
        #    raise webob.exc.HTTPBadRequest(explanation=expl)
        # else:
        try:
            migrations.migration_delete(context, id)
        except exception.MigrationNotFound as ex:
            raise webob.exc.HTTPNotFound(explanation=ex.msg)

        return webob.Response(status_int=202)


def create_resource(ext_mgr):
    return wsgi.Resource(MigrationsController(ext_mgr))
