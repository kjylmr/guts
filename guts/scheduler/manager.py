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
Guts Scheduler Service
"""

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import importutils

from guts import context
from guts import manager
from guts.migration import rpcapi as migration_rpcapi


scheduler_driver_opt = cfg.StrOpt('scheduler_driver',
                                  default='guts.scheduler.filter_scheduler.'
                                          'FilterScheduler',
                                  help='Default scheduler driver to use')

CONF = cfg.CONF
CONF.register_opt(scheduler_driver_opt)

LOG = logging.getLogger(__name__)


class SchedulerManager(manager.Manager):
    """Chooses a host to perform migration operation."""

    RPC_API_VERSION = '1.8'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, scheduler_driver=None, service_name=None,
                 *args, **kwargs):
        if not scheduler_driver:
            scheduler_driver = CONF.scheduler_driver
        self.driver = importutils.import_object(scheduler_driver)
        super(SchedulerManager, self).__init__(*args, **kwargs)
        self._startup_delay = True

    def init_host_with_rpc(self):
        ctxt = context.get_admin_context()
        self.request_service_capabilities(ctxt)

        eventlet.sleep(CONF.periodic_interval)
        self._startup_delay = False

    def reset(self):
        super(SchedulerManager, self).reset()
        self.driver.reset()

    def request_service_capabilities(self, context):
        migration_rpcapi.SourceAPI().publish_service_capabilities(context)
        migration_rpcapi.DestinationAPI().publish_service_capabilities(context)

    def update_service_capabilities(self, context, service_name=None,
                                    host=None, capabilities=None, **kwargs):
        """Process a capability update from a service node."""
        if capabilities is None:
            capabilities = {}
        self.driver.update_service_capabilities(service_name,
                                                host,
                                                capabilities)