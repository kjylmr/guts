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


db_opts = [
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create')]

CONF = cfg.CONF
CONF.register_opts(db_opts)

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


def vm_create(context, vm):
    """Create a new vm."""
    return IMPL.vm_create(context, vm)


def vm_delete(context, vm_id):
    """Deletes the given source vm."""
    return IMPL.vm_delete(context, vm_id)


def delete_vms_by_source_id(context, source_id):
    """Deletes all VMs list from the given source hypervisor."""
    return IMPL.delete_vms_by_source_id(context, source_id)


def vm_update(context, vm_id, values):
    """Set the given properties on an vm and update it.

    Raises NotFound if vm does not exist.
    """
    return IMPL.vm_update(context, vm_id, values)


def vm_get_by_name(context, name):
    """Return a dict describing specific source vm."""

    return IMPL.vm_get_by_name(context, name)


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


def migration_update(context, migration_id, values):
    """Set the given properties on an migration and update it.

    Raises NotFound if migration does not exist.
    """
    return IMPL.migration_update(context, migration_id, values)


# Service

def service_destroy(context, service_id):
    """Destroy the service or raise if it does not exist."""
    return IMPL.service_destroy(context, service_id)


def service_get(context, service_id):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get(context, service_id)


def service_get_by_host_and_topic(context, host, topic):
    """Get a service by host it's on and topic it listens to."""
    return IMPL.service_get_by_host_and_topic(context, host, topic)


def service_get_all(context, disabled=None):
    """Get all services."""
    return IMPL.service_get_all(context, disabled)


def service_get_all_by_topic(context, topic, disabled=None):
    """Get all services for a given topic."""
    return IMPL.service_get_all_by_topic(context, topic, disabled=disabled)


def service_get_by_args(context, host, binary):
    """Get the state of an service by node name and binary."""
    return IMPL.service_get_by_args(context, host, binary)


def service_create(context, values):
    """Create a service from the values dictionary."""
    return IMPL.service_create(context, values)


def service_update(context, service_id, values):
    """Updates service entry

    Set the given properties on an service and update it.
    Raises NotFound if service does not exist.
    """
    return IMPL.service_update(context, service_id, values)


# Extra


def get_model_for_versioned_object(versioned_object):
    return IMPL.get_model_for_versioned_object(versioned_object)


def get_by_id(context, model, id, *args, **kwargs):
    return IMPL.get_by_id(context, model, id, *args, **kwargs)


class Condition(object):
    """Class for normal condition values for conditional_update."""
    def __init__(self, value, field=None):
        self.value = value
        # Field is optional and can be passed when getting the filter
        self.field = field

    def get_filter(self, model, field=None):
        return IMPL.condition_db_filter(model, self._get_field(field),
                                        self.value)

    def _get_field(self, field=None):
        # We must have a defined field on initialization or when called
        field = field or self.field
        if not field:
            raise ValueError('Condition has no field.')
        return field


class Not(Condition):
    """Class for negated condition values for conditional_update.

    By default NULL values will be treated like Python treats None instead of
    how SQL treats it.

    So for example when values are (1, 2) it will evaluate to True when we have
    value 3 or NULL, instead of only with 3 like SQL does.
    """
    def __init__(self, value, field=None, auto_none=True):
        super(Not, self).__init__(value, field)
        self.auto_none = auto_none

    def get_filter(self, model, field=None):
        # If implementation has a specific method use it
        if hasattr(IMPL, 'condition_not_db_filter'):
            return IMPL.condition_not_db_filter(model, self._get_field(field),
                                                self.value, self.auto_none)

        # Otherwise non negated object must adming ~ operator for not
        return ~super(Not, self).get_filter(model, field)


class Case(object):
    """Class for conditional value selection for conditional_update."""
    def __init__(self, whens, value=None, else_=None):
        self.whens = whens
        self.value = value
        self.else_ = else_
