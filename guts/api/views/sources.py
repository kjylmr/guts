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
from guts.migration import types


class ViewBuilder(common.ViewBuilder):

    def show(self, request, context, source, brief=False):
        """Trim away extraneous source hypervisor attributes."""
        trimmed = dict(id=source.get('id'),
                       name=source.get('name'),
                       connection_params=source.get('connection_params'),
                       description=source.get('description'))

        source_type = types.get_source_type(context, source.source_type_id)
        trimmed['source_type_name'] = source_type.get('name')

        return trimmed if brief else dict(source=trimmed)

    def index(self, request, context, sources):
        """Index over trimmed source hypervisors."""
        source_list = [self.show(request, context, source, True)
                       for source in sources]
        return dict(sources=source_list)
