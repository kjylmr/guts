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

class ViewBuilder(common.ViewBuilder):
    """Model hypervisor API responces as a python dictionary"""

    _collection_name = "hypervisors"

    def __init__(self):
        """Initialize view builder."""
        super(ViewBuilder, self).__init__()

    def summary_list(self, request, hypervisors, hypervisor_count=None):
        """Show a list of hypervisors without many details."""
        return self._list_view(self.summary, request,
                               hypervisors, hypervisor_count)

    def detail_list(self, request, hypervisors, hypervisor_count=None):
        """Detailed view of a list of hypervisors."""
        return self._list_view(self.detail, request,
                               hypervisors, hypervisor_count)

    def summary(self, request, hypervisor):
        """Generic, non-detailed view of a hypervisor."""
        return {
            'hypervisor': {
                'id': hypervisor['id'],
                'name': hypervisor['name'],
                'type': hypervisor['type'],
                'driver': hypervisor['driver'].split('.')[-1],
                'capabilities': hypervisor['capabilities'],
                'status': 'Enabled' if hypervisor['enabled'] else 'Disabled',
            },
        }

    def detail(self, request, hypervisor):
        """Detailed view of a single hypervisor."""
        return {
            'hypervisor': {
                'id': hypervisor['id'],
                'name': hypervisor['name'],
                'type': hypervisor['type'],
                'driver': hypervisor['driver'],
                'capabilities': hypervisor['capabilities'],
                'status': 'Enabled' if hypervisor['enabled'] else 'Disabled',
                'created_at': hypervisor.get('created_at'),
                'updated_at': hypervisor.get('updated_at'),
                'allowed_hosts': hypervisor.get('allowed_hosts'),
                'registered_host': hypervisor.get('host'),
                'exclude_by_uuid': hypervisor.get('exclude_resource_uuids'),
                'exclude_by_names': hypervisor.get('exclude_resource_names'),
                'conversion_dir': hypervisor.get('conversion_dir'),
            }
        }

    def _list_view(self, func, request, hypervisors, hypervisor_count):
        """Provide a view for a list of hypervisor."""
        hypervisors_list = [func(request, hypervisor)['hypervisor']
                            for hypervisor in hypervisors]

        hypervisors_dict = dict(hypervisors=hypervisors_list)

        return hypervisors_dict
