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


from guts.api import common
from oslo_utils import importutils


def get_connection_params(driver_path):
    driver_path = importutils.import_module(driver_path)
    connection_params = driver_path.get_connection_params_dict()
    return connection_params


class ViewBuilder(common.ViewBuilder):

    def show(self, request, source_type, brief=False):
        """Trim away extraneous source hypervisor type attributes."""
        trimmed = dict(id=source_type.get('id'),
                       name=source_type.get('name'),
                       driver=source_type.get('driver_class_path'),
                       description=source_type.get('description'))
        trimmed['con_params'] = get_connection_params(trimmed['driver'])

        return trimmed if brief else dict(source_type=trimmed)

    def index(self, request, source_types):
        """Index over trimmed source hypervisor types."""
        source_types_list = [self.show(request, source_type, True)
                             for source_type in source_types]
        return dict(source_types=source_types_list)
