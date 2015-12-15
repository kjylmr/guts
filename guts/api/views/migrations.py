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

    def show(self, request, migration, brief=False):
        """Trim away extraneous migration attributes."""
        trimmed = dict(id=migration.get('id'),
                       name=migration.get('name'),
                       source_instance_id=migration.get('source_instance_id'),
                       status=migration.get('migration_status'),
                       event=migration.get('migration_event'),
                       description=migration.get('description'))
        return trimmed if brief else dict(migration=trimmed)

    def index(self, request, migrations):
        """Index over trimmed migrations."""
        migration_list = [self.show(request, migration, True)
                          for migration in migrations]
        return dict(migrations=migration_list)
