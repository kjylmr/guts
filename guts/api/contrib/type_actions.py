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


from oslo_config import cfg
from oslo_log import log as logging

from guts.api import extensions
from guts.api.openstack import wsgi


CONF = cfg.CONF

LOG = logging.getLogger(__name__)
authorize = extensions.extension_authorizer('types', '')


class TypeActionsController(wsgi.Controller):
    def __init__(self):
        super(TypeActionsController, self).__init__()


class Type_actions(extensions.ExtensionDescriptor):
    """Enables source hypervisor type actions."""

    name = "TypeActions"
    alias = "os-type-actions"
    namespace = ""
    updated = ""

    def get_controller_extensions(self):
        controller = TypeActionsController()
        extension = extensions.ControllerExtension(self, 'types', controller)
        return [extension]
