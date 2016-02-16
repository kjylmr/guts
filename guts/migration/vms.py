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

"""Built-in sources VM properties."""


from oslo_config import cfg
from oslo_log import log as logging

from guts import db
from guts import exception
from guts.i18n import _
from guts.migration import rpcapi as migration_rpcapi
from guts import policy


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def check_policy(context, action, target_obj=None):
    target = {
        'project_id': context.project_id,
        'user_id': context.user_id,
    }
    _action = 'vms:%s' % action
    policy.enforce(context, _action, target)


def get_all_vms(context, inactive=0):
    """Get all non-deleted source vms.

    Pass true as argument if you want deleted sources returned also.
    """
    check_policy(context, 'get_all_vms')
    return db.vm_get_all(context, inactive)


def get_vm(context, id):
    """Retrieves single source by ID."""
    if id is None:
        msg = _("ID cannot be None")
        raise exception.InvalidSource(reason=msg)

    check_policy(context, 'get_vm')
    return db.vm_get(context, id)


def get_vm_by_name(context, name):
    """Retrieves single source by name."""
    if name is None:
        msg = _("VM name cannot be None")
        raise exception.InvalidSource(reason=msg)

    return db.vm_get_by_name(context, name)


def vm_delete(context, id):
    """Deletes specified source VM."""

    return db.vm_delete(context, id)


def fetch_vms(context, source_id):
    """Fetch VMs from the source hypervisor."""
    check_policy(context, 'fetch_vms')
    migration_api = migration_rpcapi.MigrationAPI()
    migration_api.fetch_vms(context, source_id)
