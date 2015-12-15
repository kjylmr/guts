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

    def show(self, request, vm, brief=False):
        """Trim away extraneous source vm attributes."""
        trimmed = dict(id=vm.get('id'),
                       name=vm.get('name'),
                       source_id=vm.get('source_id'),
                       description=vm.get('description'))
        return trimmed if brief else dict(vm=trimmed)

    def index(self, request, vms):
        """Index over trimmed source vms."""
        vm_list = [self.show(request, vm, True) for vm in vms]
        return dict(vms=vm_list)
