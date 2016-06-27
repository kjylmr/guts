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
class Hypervisor(base.GutsPersistentObject, base.GutsObject,
               base.GutsObjectDictCompat,
               base.GutsComparableObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.StringField(),
        'name': fields.StringField(nullable=True),
        'type': fields.StringField(nullable=True),
        'driver': fields.StringField(nullable=True),
        'credentials': fields.StringField(nullable=True),
        'capabilities': fields.StringField(nullable=True),
        'exclude': fields.StringField(nullable=True),
        'registered_host': fields.StringField(nullable=True),
        'properties': fields.StringField(nullable=True),
        'conversion_dir': fields.StringField(nullable=True),
        'deleted': fields.BooleanField(default=False),
    }

    def obj_make_compatible(self, primitive, target_version):
        """Make an object representation compatible with a target version."""
        target_version = utils.convert_version_to_tuple(target_version)

    @staticmethod
    def _from_db_object(context, hypervisor, db_hypervisor):
        for name, field in hypervisor.fields.items():
            value = db_hypervisor.get(name)
            if isinstance(field, fields.IntegerField):
                value = value or 0
            elif isinstance(field, fields.DateTimeField):
                value = value or None
            hypervisor[name] = value

        hypervisor._context = context
        hypervisor.obj_reset_changes()
        return hypervisor

    @base.remotable_classmethod
    def get(cls, context, hypervisor_id):
        db_hypervisor = db.hypervisor_get(context, hypervisor_id)
        return cls._from_db_object(context, cls(context), db_hypervisor)

    @base.remotable_classmethod
    def get_by_name(cls, context, hypervisor_name):
        db_hypervisor = db.hypervisor_get_by_name(context, hypervisor_name)
        return cls._from_db_object(context, cls(context), db_hypervisor)

    @base.remotable
    def create(self):
        if self.obj_attr_is_set('id'):
            raise exception.ObjectActionError(action='create',
                                              reason=_('already created'))
        updates = self.guts_obj_get_changes()
        db_hypervisor = db.hypervisor_create(self._context, updates)
        self._from_db_object(self._context, self, db_hypervisor)

    @base.remotable
    def save(self):
        updates = self.guts_obj_get_changes()
        if updates:
            db.hypervisor_update(self._context, self.id, updates)
            self.obj_reset_changes()

    @base.remotable
    def destroy(self):
        with self.obj_as_admin():
            db.hypervisor_delete(self._context, self.id)


@base.GutsObjectRegistry.register
class HypervisorList(base.ObjectListBase, base.GutsObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Hypervisor'),
    }
    child_versions = {
        '1.0': '1.0'
    }

    @base.remotable_classmethod
    def get_all(cls, context, filters=None):
        hypervisors = db.hypervisor_get_all(context, filters)
        return base.obj_make_list(context, cls(context), objects.Hypervisor,
                                  hypervisors)

    @base.remotable_classmethod
    def get_all_by_type(cls, context, hypervisor_type, disabled=None):
        hypervisors = db.hypervisor_get_all_by_type(context, hypervisor_type)
        return base.obj_make_list(context, cls(context), objects.Hypervisor,
                                  hypervisors)
