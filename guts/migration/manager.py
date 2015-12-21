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

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from guts import manager


CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class MigrationManager(manager.Manager):
    """Creates & manages VM migrations."""

    RPC_API_VERSION = '1.11'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, service_name=None,
                 *args, **kwargs):
        super(MigrationManager, self).__init__(*args, **kwargs)

    def create_migration(self, context, migration_ref):
        # TODO(Alok): Add your code here to create new migration
        # process.
        return True

    def fetch_vms(self, context, source_hypervisor_id):
        # TODO(Alok): Add your code here to fetch VM list from
        # source hypervisor and update DB.
        return True
