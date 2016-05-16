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

"""
Manage hosts in the current zone.
"""

import collections

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from guts import context as guts_context
from guts import db
from guts import exception
from guts import objects
from guts import utils
from guts.i18n import _LI, _LW
from guts.scheduler import filters
from guts.scheduler import weights


host_manager_opts = [
    cfg.ListOpt('scheduler_default_filters',
                default=[
                    'CapacityFilter',
                    'CapabilitiesFilter'
                ],
                help='Which filter class names to use for filtering hosts '
                     'when not specified in the request.'),
    cfg.ListOpt('scheduler_default_weighers',
                default=[
                    'CapacityWeigher'
                ],
                help='Which weigher class names to use for weighing hosts.')
]

CONF = cfg.CONF
CONF.register_opts(host_manager_opts)
CONF.import_opt('scheduler_driver', 'guts.scheduler.manager')

LOG = logging.getLogger(__name__)


class ReadOnlyDict(collections.Mapping):
    """A read-only dict."""
    def __init__(self, source=None):
        if source is not None:
            self.data = dict(source)
        else:
            self.data = {}

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.data)


class HostState(object):
    """Mutable and immutable information tracked for a hosts."""

    def __init__(self, host, capabilities=None, service=None):
        self.capabilities = None
        self.service = None
        self.host = host
        self.update_capabilities(capabilities, service)

        self.migration_host_name = None
        self.total_capacity_gb = 0

        self.updated = None

    def update_capabilities(self, capabilities=None, service=None):
        # Read-only capability dicts

        if capabilities is None:
            capabilities = {}
        self.capabilities = ReadOnlyDict(capabilities)
        if service is None:
            service = {}
        self.service = ReadOnlyDict(service)

    def update_from_migration_capability(self, capability, service=None):
        """Update information about a host from its migration_node info.

        'capability' is the status info reported by migration backend, a typical
        capability looks like this:
        """
        self.update_capabilities(capability, service)

        if capability:
            if self.updated and self.updated > capability['timestamp']:
                return

    def update_backend(self, capability):
        self.volume_backend_name = capability.get('volume_backend_name', None)
        self.vendor_name = capability.get('vendor_name', None)
        self.driver_version = capability.get('driver_version', None)
        self.storage_protocol = capability.get('storage_protocol', None)
        self.updated = capability['timestamp']

    def __repr__(self):
        return ("host '%s': free_capacity_gb: %s, pools: %s" %
                (self.host, self.free_capacity_gb, self.pools))


class HostManager(object):
    """Base HostManager class."""

    host_state_cls = HostState

    def __init__(self):
        self.service_states = {}  # { <host>: {<service>: {cap k : v}}}
        self.host_state_map = {}
        self.filter_handler = filters.HostFilterHandler('guts.scheduler.'
                                                        'filters')
        self.filter_classes = self.filter_handler.get_all_classes()
        self.weight_handler = weights.HostWeightHandler('guts.scheduler.'
                                                        'weights')
        self.weight_classes = self.weight_handler.get_all_classes()

        self._no_capabilities_hosts = set()  # Hosts having no capabilities
        self._context = guts_context.get_admin_context()
        self._update_host_state_map(self._context)

    def _choose_host_filters(self, filter_cls_names):
        """Return a list of available filter names.

        This function checks input filter names against a predefined set
        of acceptable filters (all loaded filters).  If input is None,
        it uses CONF.scheduler_default_filters instead.
        """
        if filter_cls_names is None:
            filter_cls_names = CONF.scheduler_default_filters
        if not isinstance(filter_cls_names, (list, tuple)):
            filter_cls_names = [filter_cls_names]
        good_filters = []
        bad_filters = []
        for filter_name in filter_cls_names:
            found_class = False
            for cls in self.filter_classes:
                if cls.__name__ == filter_name:
                    found_class = True
                    good_filters.append(cls)
                    break
            if not found_class:
                bad_filters.append(filter_name)
        if bad_filters:
            raise exception.SchedulerHostFilterNotFound(
                filter_name=", ".join(bad_filters))
        return good_filters

    def _choose_host_weighers(self, weight_cls_names):
        """Return a list of available weigher names.

        This function checks input weigher names against a predefined set
        of acceptable weighers (all loaded weighers).  If input is None,
        it uses CONF.scheduler_default_weighers instead.
        """
        if weight_cls_names is None:
            weight_cls_names = CONF.scheduler_default_weighers
        if not isinstance(weight_cls_names, (list, tuple)):
            weight_cls_names = [weight_cls_names]

        good_weighers = []
        bad_weighers = []
        for weigher_name in weight_cls_names:
            found_class = False
            for cls in self.weight_classes:
                if cls.__name__ == weigher_name:
                    good_weighers.append(cls)
                    found_class = True
                    break
            if not found_class:
                bad_weighers.append(weigher_name)
        if bad_weighers:
            raise exception.SchedulerHostWeigherNotFound(
                weigher_name=", ".join(bad_weighers))
        return good_weighers

    def get_filtered_hosts(self, hosts, filter_properties,
                           filter_class_names=None):
        """Filter hosts and return only ones passing all filters."""
        filter_classes = self._choose_host_filters(filter_class_names)
        return self.filter_handler.get_filtered_objects(filter_classes,
                                                        hosts,
                                                        filter_properties)

    def get_weighed_hosts(self, hosts, weight_properties,
                          weigher_class_names=None):
        """Weigh the hosts."""
        weigher_classes = self._choose_host_weighers(weigher_class_names)
        return self.weight_handler.get_weighed_objects(weigher_classes,
                                                       hosts,
                                                       weight_properties)

    def update_service_capabilities(self, service_name, host, capabilities):
        """Update the per-service capabilities based on this notification."""
        if not (service_name != 'source' or service_name != 'destination'):
            LOG.debug('Ignoring %(service_name)s service update '
                      'from %(host)s',
                      {'service_name': service_name, 'host': host})
            return

        if service_name == 'source':
            resources = capabilities['resources']
            # objects.ResourceList.delete_all_by_source(self._context, host)
            for capab in resources.keys():
                if capab not in capabilities['capabilities']:
                    continue
                for resource in resources[capab]:
                    try:
                        objects.Resource.get_by_id_at_source(self._context,
                                                             resource.get('id'))
                    except exception.ResourceNotFound:
                        pass
                    else:
                        continue
                    kwargs = {'type': capab,
                              'source': host,
                              'name': resource.get('name'),
                              'id_at_source': resource.get('id'),
                              'properties': str(resource)}
                    resource_ref = objects.Resource(context=self._context,
                                                    **kwargs)
                    resource_ref.create()
            
        # Copy the capabilities, so we don't modify the original dict
        capab_copy = dict(capabilities)
        capab_copy["timestamp"] = timeutils.utcnow()  # Reported time

        self.service_states[host] = capab_copy

        LOG.debug("Received %(service_name)s service update from "
                  "%(host)s: %(cap)s",
                  {'service_name': service_name, 'host': host,
                   'cap': capabilities})

        self._no_capabilities_hosts.discard(host)

    def has_all_capabilities(self):
        return len(self._no_capabilities_hosts) == 0

    def _update_host_state_map(self, context):

        # Get resource usage across the available nodes:
        sources = objects.ServiceList.get_all_by_topic(context,
                                                       CONF.source_topic,
                                                       disabled=False)
        dests = objects.ServiceList.get_all_by_topic(context,
                                                     CONF.destination_topic,
                                                     disabled=False)
        active_hosts = set()
        no_capabilities_hosts = set()
        for service in sources.objects + dests.objects:
            host = service.host
            if not utils.service_is_up(service):
                LOG.warning(_LW("Service is down. (host: %s)"), host)
                continue
            capabilities = self.service_states.get(host, None)
            if capabilities is None:
                no_capabilities_hosts.add(host)
                continue

            host_state = self.host_state_map.get(host)
            if not host_state:
                host_state = self.host_state_cls(host,
                                                 capabilities=capabilities,
                                                 service=
                                                 dict(service))
                self.host_state_map[host] = host_state
            # update capabilities and attributes in host_state
            host_state.update_from_migration_capability(capabilities,
                                                     service=
                                                     dict(service))
            active_hosts.add(host)

        self._no_capabilities_hosts = no_capabilities_hosts

        # remove non-active hosts from host_state_map
        nonactive_hosts = set(self.host_state_map.keys()) - active_hosts
        for host in nonactive_hosts:
            LOG.info(_LI("Removing non-active host: %(host)s from "
                         "scheduler cache."), {'host': host})
            del self.host_state_map[host]

    def get_all_host_states(self, context):
        """Returns a dict of all the hosts the HostManager knows about.

        Each of the consumable resources in HostState are
        populated with capabilities scheduler received from RPC.

        For example:
          {'192.168.1.100': HostState(), ...}
        """

        self._update_host_state_map(context)

        # build a pool_state map and return that map instead of host_state_map
        all_pools = {}
        for host, state in self.host_state_map.items():
            for key in state.pools:
                pool = state.pools[key]
                # use host.pool_name to make sure key is unique
                pool_key = '.'.join([host, pool.pool_name])
                all_pools[pool_key] = pool

        return all_pools.values()
