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
Scheduler base class that all Schedulers should inherit from
"""

from oslo_config import cfg
from oslo_utils import importutils
from oslo_utils import timeutils

from guts.i18n import _
from guts import objects
from guts.migration import rpcapi as migration_rpcapi


scheduler_driver_opts = [
    cfg.StrOpt('scheduler_host_manager',
               default='guts.scheduler.host_manager.HostManager',
               help='The scheduler host manager class to use'),
    cfg.IntOpt('scheduler_max_attempts',
               default=3,
               help='Maximum number of attempts to schedule a migration'),
]

CONF = cfg.CONF
CONF.register_opts(scheduler_driver_opts)


class Scheduler(object):
    """The base class that all Scheduler classes should inherit from."""

    def __init__(self):
        self.host_manager = importutils.import_object(
            CONF.scheduler_host_manager)
        self.source_rpcapi = migration_rpcapi.SourceAPI()
        self.destination_rpcapi = migration_rpcapi.DestinationAPI()

    def reset(self):
        """Reset migration RPC API object to load new version pins."""
        self.source_rpcapi = migration_rpcapi.SourceAPI()
        self.destination_rpcapi = migration_rpcapi.DestinationAPI()

    def is_ready(self):
        """Returns True if Scheduler is ready to accept requests.

        This is to handle scheduler service startup when it has no migration hosts
        stats and will fail all the requests.
        """
        return self.host_manager.has_all_capabilities()

    def update_service_capabilities(self, service_name, host, capabilities):
        """Process a capability update from a service node."""
        self.host_manager.update_service_capabilities(service_name,
                                                      host,
                                                      capabilities)

    def host_passes_filters(self, context, migration_id, host, filter_properties):
        """Check if the specified host passes the filters."""
        raise NotImplementedError(_("Must implement host_passes_filters"))

    def schedule(self, context, topic, method, *_args, **_kwargs):
        """Must override schedule method for scheduler to work."""
        raise NotImplementedError(_("Must implement a fallback schedule"))

    def schedule_create_migration(self, context, request_spec, filter_properties):
        """Must override schedule method for scheduler to work."""
        raise NotImplementedError(_("Must implement schedule_create_migration"))
