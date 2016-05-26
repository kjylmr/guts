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
Client side of the scheduler manager RPC API.
"""

from oslo_config import cfg

from guts import rpc


CONF = cfg.CONF


class SchedulerAPI(rpc.RPCAPI):
    """Guts side of the scheduler rpc API."""

    RPC_API_VERSION = '2.0'
    TOPIC = CONF.scheduler_topic
    BINARY = 'guts-scheduler'

    def update_service_capabilities(self, ctxt,
                                    service_name, host,
                                    capabilities):
        cctxt = self.client.prepare(fanout=True, version='1.8')
        cctxt.cast(ctxt, 'update_service_capabilities',
                   service_name=service_name, host=host,
                   capabilities=capabilities)
