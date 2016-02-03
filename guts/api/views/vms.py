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
from guts.migration import sources


class ViewBuilder(common.ViewBuilder):

    def show(self, request, context, vm, brief=False):
        """Trim away extraneous source vm attributes."""
        trimmed = dict(id=vm.get('id'),
                       name=vm.get('name'),
                       uuid_at_source=vm.get('uuid_at_source'),
                       migrated=vm.get('migrated'),
                       destination_vm_id=vm.get('dest_id'))
        src = sources.get_source(context, vm.get('source_id'))
        trimmed['hypervisor_name'] = src.get('name')
        return trimmed if brief else dict(vm=trimmed)

    def index(self, request, context, vms):
        """Index over trimmed source vms."""
        vm_list = [self.show(request, context, vm, True) for vm in vms]
        return dict(vms=vm_list)
