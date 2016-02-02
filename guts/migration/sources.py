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

"""Built-in sources properties."""


from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging

from guts import context
from guts import db
from guts import exception
from guts.i18n import _, _LE


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_all_sources(ctxt, inactive=0):
    """Get all non-deleted source hypervisors.

    Pass true as argument if you want deleted sources returned also.

    """
    return db.source_get_all(ctxt, inactive)


def get_source(ctxt, id):
    """Retrieves single source by ID."""
    if id is None:
        msg = _("ID cannot be None")
        raise exception.InvalidSource(reason=msg)

    if ctxt is None:
        ctxt = context.get_admin_context()

    return db.source_get(ctxt, id)


def create(ctxt, name, stype, connection_params, description=None):
    """Creates source."""
    try:
        source_ref = db.source_create(ctxt,
                                      dict(name=name, source_type_id=stype,
                                           connection_params=connection_params,
                                           description=description))
    except db_exc.DBError:
        LOG.exception(_LE('DB error:'))
        raise exception.SourceCreateFailed(name=name)

    return source_ref


def get_source_by_name(context, name):
    """Retrieves single source by name."""
    if name is None:
        msg = _("Source name cannot be None")
        raise exception.InvalidSource(reason=msg)

    return db.source_get_by_name(context, name)


def source_delete(context, id):
    """Deletes specified source."""
    db.delete_vms_by_source_id(context, id)
    return db.source_delete(context, id)
