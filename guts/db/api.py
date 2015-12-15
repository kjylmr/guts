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

"""Defines interface for DB access.

Functions in this module are imported into the guts.db namespace. Call these
functions from guts.db namespace, not the guts.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.


**Related Flags**

:connection:  string specifying the sqlalchemy connection to use, like:
              `sqlite:///var/lib/guts/guts.sqlite`.

:enable_new_services:  when adding a new service to the database, is it in the
                       pool of available hardware (Default: True)

"""

from oslo_config import cfg
from oslo_db import concurrency as db_concurrency


CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'guts.db.sqlalchemy.api'}
IMPL = db_concurrency.TpoolDbapiWrapper(CONF, _BACKEND_MAPPING)


def dispose_engine():
    """Force the engine to establish new connections."""

    if 'sqlite' not in IMPL.get_engine().name:
        return IMPL.dispose_engine()
    else:
        return


def purge_deleted_rows(context, age_in_days):
    """Purge deleted rows older than given age from guts tables

    Raises InvalidParameterValue if age_in_days is incorrect.

    :returns: number of deleted rows
    """
    return IMPL.purge_deleted_rows(context, age_in_days=age_in_days)


# Source Types

def source_type_get_all(context, inactive=False):
    """Get all source hypervisor types.

    :param context: context to query under
    :param inactive: Include inactive source types to the result set

    :returns: list of source hypervisor types
    """
    return IMPL.source_type_get_all(context, inactive)


def source_type_get(context, id):
    """Get source hypervisor type by ID.

    :param context: context to query under
    :param id: Source type id to get.

    :returns: source hypervisor type
    """
    return IMPL.source_type_get(context, id)


def source_type_create(context, values):
    """Create a new source type."""
    return IMPL.source_type_create(context, values)


def source_type_get_by_name(context, name):
    """Get source type by name."""
    return IMPL.source_type_get_by_name(context, name)


def source_type_delete(context, type_id):
    """Deletes the given source type."""
    return IMPL.source_type_delete(context, type_id)


# Sources

def source_get_all(context, inactive=False):
    """Get all source hypervisors.

    :param context: context to query under
    :param inactive: Include inactive sources to the result set

    :returns: list of source hypervisors
    """
    return IMPL.source_get_all(context, inactive)


def source_get(context, id):
    """Get source hypervisor by ID.

    :param context: context to query under
    :param id: Source id to get.

    :returns: source hypervisor
    """
    return IMPL.source_get(context, id)


def source_create(context, values):
    """Create a new source."""
    return IMPL.source_create(context, values)


def source_get_by_name(context, name):
    """Get source by name."""
    return IMPL.source_get_by_name(context, name)


def source_delete(context, source_id):
    """Deletes the given source."""
    return IMPL.source_delete(context, source_id)


# VMs

def vm_get_all(context, inactive=False):
    """Get all source vms.

    :param context: context to query under
    :param inactive: Include inactive sources to the result set

    :returns: list of source vms
    """
    return IMPL.vm_get_all(context, inactive)


def vm_get(context, id):
    """Get source vm by ID.

    :param context: context to query under
    :param id: Source VM id to get.

    :returns: source vm
    """
    return IMPL.vm_get(context, id)


def vm_delete(context, vm_id):
    """Deletes the given source vm."""
    return IMPL.vm_delete(context, vm_id)


# Migrations


def migration_get_all(context, inactive=False):
    """Get all migrations."""
    return IMPL.migration_get_all(context, inactive)


def migration_get(context, id):
    """Get Migration."""
    return IMPL.migration_get(context, id)


def migration_delete(context, migration_id):
    """Deletes the given migration."""
    return IMPL.migration_delete(context, migration_id)


def migration_create(context, values):
    """Create a new migration."""
    return IMPL.migration_create(context, values)


def migration_get_by_name(context, name):
    """Migration get by name"""
    return IMPL.migration_get_by_name(context, name)
