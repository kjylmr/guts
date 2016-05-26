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
class Resource(base.GutsPersistentObject, base.GutsObject,
               base.GutsObjectDictCompat,
               base.GutsComparableObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.StringField(),
        'id_at_source': fields.StringField(nullable=True),
        'name': fields.StringField(nullable=True),
        'type': fields.StringField(nullable=True),
        'source': fields.StringField(nullable=True),
        'properties': fields.StringField(nullable=True),
        'migrated': fields.BooleanField(default=False),
        'deleted': fields.BooleanField(default=False),
    }

    def obj_make_compatible(self, primitive, target_version):
        """Make an object representation compatible with a target version."""
        target_version = utils.convert_version_to_tuple(target_version)

    @staticmethod
    def _from_db_object(context, resource, db_service):
        for name, field in resource.fields.items():
            value = db_service.get(name)
            if isinstance(field, fields.IntegerField):
                value = value or 0
            elif isinstance(field, fields.DateTimeField):
                value = value or None
            resource[name] = value

        resource._context = context
        resource.obj_reset_changes()
        return resource

    @base.remotable_classmethod
    def get_by_id_at_source(cls, context, id_at_source):
        db_resource = db.resource_get_by_id_at_source(context, id_at_source)
        return cls._from_db_object(context, cls(context), db_resource)

    @base.remotable_classmethod
    def get(cls, context, resource_id):
        db_resource = db.resource_get(context, resource_id)
        return cls._from_db_object(context, cls(context), db_resource)

    @base.remotable
    def create(self):
        if self.obj_attr_is_set('id'):
            raise exception.ObjectActionError(action='create',
                                              reason=_('already created'))
        updates = self.guts_obj_get_changes()
        db_resource = db.resource_create(self._context, updates)
        self._from_db_object(self._context, self, db_resource)

    @base.remotable
    def save(self):
        updates = self.guts_obj_get_changes()
        if updates:
            db.resource_update(self._context, self.id, updates)
            self.obj_reset_changes()

    @base.remotable
    def destroy(self):
        with self.obj_as_admin():
            db.resource_delete(self._context, self.id)


@base.GutsObjectRegistry.register
class ResourceList(base.ObjectListBase, base.GutsObject):
    VERSION = '1.0'

    fields = {
        'objects': fields.ListOfObjectsField('Resource'),
    }
    child_versions = {
        '1.0': '1.0'
    }

    @base.remotable_classmethod
    def get_all(cls, context, filters=None):
        resources = db.resource_get_all(context, filters)
        return base.obj_make_list(context, cls(context), objects.Resource,
                                  resources)

    @base.remotable_classmethod
    def get_all_by_type(cls, context, resource_type, disabled=None):
        resources = db.resource_get_all_by_type(context, resource_type)
        return base.obj_make_list(context, cls(context), objects.Resource,
                                  resources)

    @base.remotable_classmethod
    def get_all_by_source(cls, context, source, disabled=None):
        resources = db.resource_get_all_by_source(context, source)
        return base.obj_make_list(context, cls(context), objects.Resource,
                                  resources)

    @base.remotable_classmethod
    def delete_all_by_source(cls, context, source, disabled=None):
        db.resource_delete_all_by_source(context, source)
