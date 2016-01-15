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


"""
Migration Service
"""

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import importutils

from guts import manager
from guts.db.sqlalchemy import api as db_api


LOG = logging.getLogger(__name__)


class MigrationManager(manager.Manager):
    """Creates & manages VM migrations."""

    RPC_API_VERSION = '1.11'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, service_name=None,
                 *args, **kwargs):
        super(MigrationManager, self).__init__(*args, **kwargs)

    def create_migration(self, ctxt, migration_info, vm_uuid,
                         source_hypervisor_id):
        LOG.debug('creating migration for vm : %s' % vm_uuid)
        driver_module = get_driver_module(source_hypervisor_id)
        return getattr(driver_module, 'create_migration')(ctxt,
                                                          migration_info,
                                                          vm_uuid,
                                                          source_hypervisor_id)

    def fetch_vms(self, ctxt, source_hypervisor_id):
        LOG.debug('fetching vms for hypervisor : %s ' % source_hypervisor_id)
        driver_module = get_driver_module(source_hypervisor_id)
        vms = getattr(driver_module, 'get_all_vms', ctxt, source_hypervisor_id)
        for vm in vms:
            db_api.vm_create(ctxt, dict(name=vm['name'],
                                        source_id=source_hypervisor_id,
                                        description=vm['uuid']))


def get_driver_module(source_hypervisor_id):
    # TODO: figure out corresponding driver and auth params based on
    # source_id and call create_migration of the driver class.

    # TODO: Change this way and use as stated above
    migration_driver = 'guts.migration.drivers.vsphere'
    return importutils.import_module(migration_driver)
