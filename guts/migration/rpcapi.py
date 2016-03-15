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
Client side of the migration RPC API.
"""

from oslo_config import cfg
import oslo_messaging as messaging

from guts.objects import base as objects_base
from guts import rpc


CONF = cfg.CONF


class MigrationAPI(object):
    """Client side of the migration rpc API."""

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(MigrationAPI, self).__init__()
        target = messaging.Target(topic=CONF.migration_topic,
                                  version=self.BASE_RPC_API_VERSION)
        serializer = objects_base.GutsObjectSerializer()

        self.client = rpc.get_client(target, version_cap=None,
                                     serializer=serializer)

    def validate_for_migration(self, ctxt, migration_ref):
        cctxt = self.client.prepare(version='1.8')
        return cctxt.call(ctxt, 'validate_for_migration',
                          migration_ref=migration_ref)

    def create_migration(self, ctxt, migration_ref):
        cctxt = self.client.prepare(version='1.8')
        cctxt.cast(ctxt, 'create_migration', migration_ref=migration_ref)

    def fetch_vms(self, ctxt, source_hypervisor_id):
        cctxt = self.client.prepare(version='1.8')
        cctxt.cast(ctxt, 'fetch_vms',
                   source_hypervisor_id=source_hypervisor_id)
