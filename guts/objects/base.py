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

"""Guts common internal object model"""

import contextlib
import datetime

from oslo_log import log as logging
from oslo_versionedobjects import base
from oslo_versionedobjects import fields

from guts import exception
from guts import objects


LOG = logging.getLogger('object')
remotable = base.remotable
remotable_classmethod = base.remotable_classmethod
obj_make_list = base.obj_make_list


class GutsObjectRegistry(base.VersionedObjectRegistry):
    def registration_hook(self, cls, index):
        setattr(objects, cls.obj_name(), cls)


class GutsObject(base.VersionedObject):
    OBJ_PROJECT_NAMESPACE = 'guts'

    VERSION_COMPATIBILITY = {'1.0.0': '1.0'}

    def guts_obj_get_changes(self):
        """Returns a dict of changed fields with tz unaware datetimes.

        Any timezone aware datetime field will be converted to UTC timezone
        and returned as timezone unaware datetime.

        This will allow us to pass these fields directly to a db update
        method as they can't have timezone information.
        """
        # Get dirtied/changed fields
        changes = self.obj_get_changes()

        # Look for datetime objects that contain timezone information
        for k, v in changes.items():
            if isinstance(v, datetime.datetime) and v.tzinfo:
                # Remove timezone information and adjust the time according to
                # the timezone information's offset.
                changes[k] = v.replace(tzinfo=None) - v.utcoffset()

        # Return modified dict
        return changes


class GutsObjectDictCompat(base.VersionedObjectDictCompat):
    """Mix-in to provide dictionary key access compat.

    If an object needs to support attribute access using
    dictionary items instead of object attributes, inherit
    from this class. This should only be used as a temporary
    measure until all callers are converted to use modern
    attribute access.
    """

    def get(self, key, value=base._NotSpecifiedSentinel):
        """For backwards-compatibility with dict-based objects."""
        if key not in self.obj_fields:
            LOG.debug('Guts object %(object_name)s has no '
                      'attribute named: %(attribute_name)s',
                      {'object_name': self.__class__.__name__,
                       'attribute_name': key})
            return None
        if (value != base._NotSpecifiedSentinel and
                not self.obj_attr_is_set(key)):
            return value
        else:
            return getattr(self, key)


class GutsPersistentObject(object):
    """Mixin class for Persistent objects.

    This adds the fields that we use in common for all persistent objects.
    """
    fields = {
        'created_at': fields.DateTimeField(nullable=True),
        'updated_at': fields.DateTimeField(nullable=True),
        'deleted_at': fields.DateTimeField(nullable=True),
        'deleted': fields.BooleanField(default=False),
    }

    @contextlib.contextmanager
    def obj_as_admin(self):
        """Context manager to make an object call as an admin.

        This temporarily modifies the context embedded in an object to
        be elevated() and restores it after the call completes. Example
        usage:

           with obj.obj_as_admin():
               obj.save()
        """
        if self._context is None:
            raise exception.OrphanedObjectError(method='obj_as_admin',
                                                objtype=self.obj_name())

        original_context = self._context
        self._context = self._context.elevated()
        try:
            yield
        finally:
            self._context = original_context


class GutsComparableObject(base.ComparableVersionedObject):
    def __eq__(self, obj):
        if hasattr(obj, 'obj_to_primitive'):
            return self.obj_to_primitive() == obj.obj_to_primitive()
        return False


class ObjectListBase(base.ObjectListBase):
    pass


class GutsObjectSerializer(base.VersionedObjectSerializer):
    OBJ_BASE_CLASS = GutsObject
