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

"""Built-in sources properties."""

import six

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
import oslo_messaging as messaging

from guts import db
from guts import exception
from guts import policy
from guts.i18n import _, _LE
from guts.migration import rpcapi as migration_rpcapi

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def check_policy(ctxt, action, target_obj=None):
    target = {
        'project_id': ctxt.project_id,
        'user_id': ctxt.user_id,
    }
    _action = 'migrations:%s' % action
    policy.enforce(ctxt, _action, target)


def get_all_migrations(ctxt, inactive=0):
    """Get all non-deleted source hypervisors.

    Pass true as argument if you want deleted sources returned also.
    """
    check_policy(ctxt, 'get_all_migrations')
    return db.migration_get_all(ctxt, inactive)


def get_migration(ctxt, id):
    """Retrieves single source by ID."""
    if id is None:
        msg = _("ID cannot be None")
        raise exception.InvalidSource(reason=msg)
    check_policy(ctxt, 'get_migration')
    return db.migration_get(ctxt, id)


def update_migration(ctxt, id, values):
    """Updates migration DB entry"""
    # Ex: values = {"migration_status": "INCOMPLETE",
    #               "migration_event": "DOWNLOADING"}

    db.migration_update(ctxt, id, values)


def create(ctxt, name, source_instance_id, description=None):
    """Creates migration.

    Raises:
        MigrationCreateFailed: If there is error during migration creation.
        InstanceNotReadyForMigration: Migrating instance failed
                                        pre-migration validations
    """
    try:
        migration_ref = db.migration_create(
            ctxt,
            dict(name=name,
                 source_instance_id=source_instance_id,
                 description=description))
    except db_exc.DBError:
        LOG.exception(_LE('DB error:'))
        raise exception.MigrationCreateFailed(name=name)

    migration_api = migration_rpcapi.MigrationAPI()

    try:
        migration_api.validate_for_migration(ctxt, migration_ref)
    except messaging.RemoteError as ex:
        raise exception.InstanceNotReadyForMigration(
            name=name,
            reason=six.text_type(ex.value)
        )

    migration_api.create_migration(ctxt, migration_ref)

    return migration_ref


def get_migration_by_name(ctxt, name):
    """Retrieves single source by name."""
    if name is None:
        msg = _("Source name cannot be None")
        raise exception.InvalidSource(reason=msg)

    return db.migration_get_by_name(ctxt, name)


def migration_delete(ctxt, id):
    """Deletes specified source."""

    return db.migration_delete(ctxt, id)
