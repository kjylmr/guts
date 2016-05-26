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
WSGI middleware for OpenStack Migration API.
"""

from oslo_log import log as logging

from guts.api import extensions
import guts.api.openstack
from guts.api.v1 import destinations
from guts.api.v1 import instances
from guts.api.v1 import migrations
from guts.api.v1 import networks
from guts.api.v1 import resources
from guts.api.v1 import sources
from guts.api.v1 import volumes


LOG = logging.getLogger(__name__)


class APIRouter(guts.api.openstack.APIRouter):
    """Routes requests on the API to the appropriate controller and method."""
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr):
        mapper.redirect("", "/")

        self.resources['sources'] = sources.create_resource(ext_mgr)
        mapper.resource("source", "sources",
                        controller=self.resources['sources'])

        self.resources['destinations'] = destinations.create_resource(ext_mgr)
        mapper.resource("destination", "destinations",
                        controller=self.resources['destinations'])

        self.resources['resources'] = resources.create_resource(ext_mgr)
        mapper.resource("resource", "resources",
                        controller=self.resources['resources'])

        self.resources['instances'] = instances.create_resource(ext_mgr)
        mapper.resource("instance", "instances",
                        controller=self.resources['instances'])

        self.resources['volumes'] = volumes.create_resource(ext_mgr)
        mapper.resource("volume", "volumes",
                        controller=self.resources['volumes'])

        self.resources['networks'] = networks.create_resource(ext_mgr)
        mapper.resource("network", "networks",
                        controller=self.resources['networks'])

        self.resources['migrations'] = migrations.create_resource(ext_mgr)
        mapper.resource("migration", "migrations",
                        controller=self.resources['migrations'])
