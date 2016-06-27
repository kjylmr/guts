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
from oslo_versionedobjects import fields

from guts import db
from guts import exception
from guts.i18n import _
from guts import objects
from guts.objects import base
from guts import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@base.GutsObjectRegistry.register
class Migration(base.GutsPersistentObject, base.GutsObject,
                base.GutsObjectDictCompat,
                base.GutsComparableObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.StringField(),
        'name': fields.StringField(nullable=True),
        'description': fields.StringField(nullable=True),
        'resource_id': fields.StringField(nullable=True),
        'migration_status': fields.StringField(nullable=True),
        'migration_event': fields.StringField(nullable=True),
        'destination_hypervisor': fields.StringField(nullable=True),
        'extra_params': fields.StringField(nullable=True),
    }

    def obj_make_compatible(self, primitive, target_version):
        """Make an object representation compatible with a target version."""
        target_version = utils.convert_version_to_tuple(target_version)

    @staticmethod
    def _from_db_object(context, migration, db_migration):
        for name, field in migration.fields.items():
            value = db_migration.get(name)
            if isinstance(field, fields.IntegerField):
                value = value or 0
            elif isinstance(field, fields.DateTimeField):
                value = value or None
            migration[name] = value

        migration._context = context
        migration.obj_reset_changes()
        return migration

    @base.remotable_classmethod
    def get(cls, context, migration_id):
        db_migration = db.migration_get(context, migration_id)
        return cls._from_db_object(context, cls(context), db_migration)

    @base.remotable
    def create(self):
        if self.obj_attr_is_set('id'):
            raise exception.ObjectActionError(action='create',
                                              reason=_('already created'))
        updates = self.guts_obj_get_changes()
        db_migration = db.migration_create(self._context, updates)
        self._from_db_object(self._context, self, db_migration)

    @base.remotable
    def save(self):
        updates = self.guts_obj_get_changes()
        if updates:
            db.migration_update(self._context, self.id, updates)
            self.obj_reset_changes()

    @base.remotable
    def destroy(self):
        with self.obj_as_admin():
            db.migration_delete(self._context, self.id)


@base.GutsObjectRegistry.register
class MigrationList(base.ObjectListBase, base.GutsObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Migration'),
    }
    child_versions = {
        '1.0': '1.0'
    }

    @base.remotable_classmethod
    def get_all(cls, context, filters=None):
        migrations = db.migration_get_all(context, filters)
        return base.obj_make_list(context, cls(context), objects.Migration,
                                  migrations)
