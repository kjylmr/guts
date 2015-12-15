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

"""Built-in migration type properties."""


from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging

from guts import context
from guts import db
from guts import exception
from guts.i18n import _, _LE


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_all_types(ctxt, inactive=0):
    """Get all non-deleted source hypervisor types."""
    return db.source_type_get_all(ctxt, inactive)


def get_source_type(ctxt, id):
    """Retrieves single source type by ID."""
    if id is None:
        msg = _("ID cannot be None")
        raise exception.InvalidSourceType(reason=msg)

    if ctxt is None:
        ctxt = context.get_admin_context()

    return db.source_type_get(ctxt, id)


def create(ctxt, name, driver, description=None):
    """Creates source types."""
    try:
        type_ref = db.source_type_create(ctxt,
                                         dict(name=name,
                                              driver_class_path=driver,
                                              description=description))
    except db_exc.DBError:
        LOG.exception(_LE('DB error:'))
        raise exception.SourceTypeCreateFailed(name=name)

    return type_ref


def get_source_type_by_name(context, name):
    """Retrieves single source type by name."""
    if name is None:
        msg = _("Source type name cannot be None")
        raise exception.InvalidSourceType(reason=msg)

    return db.source_type_get_by_name(context, name)


def source_type_delete(context, id):
    """Deletes specified source type."""

    return db.source_type_delete(context, id)
