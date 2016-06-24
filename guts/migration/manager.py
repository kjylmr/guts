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
Migration Service
"""

import ast
import functools

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import periodic_task
from oslo_utils import importutils

from guts import context
from guts import exception
from guts.migration import configuration as config
from guts.i18n import _, _LI, _LE
from guts import manager
from guts import objects
from guts.objects import base as objects_base
from guts import rpc
from guts import utils


source_manager_opts = [
    cfg.StrOpt('source_driver',
               default='guts.migration.drivers.sources.openstack.'
                       'OpenStackSourceDriver',
               help='Driver to use for source hypervisor'),
    cfg.StrOpt('conversion_dir',
               default='$state_path/migrations',
               help='Disk conversion directory.'),
    cfg.StrOpt('capabilities',
               default='instance',
               help='Specifies types of migrations this driver supports.'),
    cfg.StrOpt('exclude',
               default='',
               help='List of resource to be excluded from migration'),
    cfg.StrOpt('nova_api_version',
               default='2',
               help='Shows the client version.'),
    cfg.StrOpt('cinder_api_version',
               default='1',
               help='Cinder client version.'),
    cfg.StrOpt('glance_api_version',
               default='1',
               help='Glance client version.'),
]

destination_manager_opts = [
    cfg.StrOpt('destination_driver',
               default='guts.migration.drivers.destinations.openstack.\
OpenStackDestinationDriver',
               help='Driver to use for destination hypervisor'),
    cfg.StrOpt('conversion_dir',
               default='$state_path/migrations',
               help='Disk conversion directory.'),
    cfg.StrOpt('capabilities',
               default='instance',
               help='Specifies types of migrations this driver supports.'),
    cfg.StrOpt('nova_api_version',
               default='2',
               help='Shows the client version.'),
    cfg.StrOpt('cinder_api_version',
               default='1',
               help='Cinder client version.'),
    cfg.StrOpt('glance_api_version',
               default='1',
               help='Glance client version.'),
]

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

get_notifier = functools.partial(rpc.get_notifier, service='migration')
wrap_exception = functools.partial(exception.wrap_exception,
                                   get_notifier=get_notifier)


def _cast_to_destination(context, dest_host, method, migration_ref,
                         resource_ref, **kwargs):
    dest_topic = ('guts-destination.%s' % (dest_host))
    target = messaging.Target(topic=dest_topic,
                              version='1.8')
    serializer = objects_base.GutsObjectSerializer()
    client = rpc.get_client(target, version_cap=None,
                            serializer=serializer)

    ctxt = client.prepare(version='1.8')
    ctxt.cast(context, method, migration_ref=migration_ref,
              resource_ref=resource_ref, **kwargs)


def _get_free_space(conversion_dir):
    """Calculate and return free space available."""
    try:
        out = utils.execute('df', '--portability', '--block-size', '1',
                            conversion_dir,
                            run_as_root=True)[0]
        out = out.splitlines()[1]
        available = int(out.split()[3])
    except Exception:
        msg = _("Failed to get the available free space.")
        LOG.exception(msg)
        raise exception.GutsException(msg)

    return available


def locked_migration_operation(f):
    """Lock decorator for migration operations.

    Takes a named lock prior to executing the migration operation. The lock is
    named with the operation executed and the id of the source VM. This lock
    can then be used by other operations to avoid operation conflicts on shared
    resources.

    Example use:
    If a migration operation uses this decorator, it will block until the named
    lock is free. This is used to protect concurrent migration operations of
    the same source VM.
    """
    def lvo_inner1(inst, context, migration_ref, **kwargs):
        source_vm_id = migration_ref.get('source_instance_id')

        @utils.synchronized("%s-%s" % (source_vm_id, f.__name__),
                            external=True)
        def lvo_inner2(*_args, **_kwargs):
            return f(*_args, **_kwargs)
        return lvo_inner2(inst, context, migration_ref, **kwargs)
    return lvo_inner1


class SourceManager(manager.SchedulerDependentManager):
    """Manages source hypervisors."""

    RPC_API_VERSION = '1.8'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, source_driver=None, service_name=None,
                 *args, **kwargs):
        """Load the source driver."""
        # updated_service_capabilities needs service_name to be "source".
        super(SourceManager, self).__init__(service_name='source',
                                            *args, **kwargs)
        self.configuration = config.Configuration(source_manager_opts,
                                                  config_group=service_name)
        self.stats = {}

        if not source_driver:
            # Get from configuration, which will get the default
            # if its not using the multi backend.
            source_driver = self.configuration.source_driver

        svc_host = utils.extract_host(self.host)
        try:
            objects.Service.get_by_args(context.get_admin_context(),
                                        svc_host, 'guts-source')
        except exception.ServiceNotFound:
            LOG.info(_LI("Service not found for updating."))
        self.driver = importutils.import_object(
            source_driver,
            configuration=self.configuration,
            host=self.host)

    def init_host(self):
        """Perform any required initialization."""
        ctxt = context.get_admin_context()

        LOG.info(_LI("Starting source driver %(driver_name)s."),
                 {'driver_name': self.driver.__class__.__name__})
        try:
            self.driver.do_setup(ctxt)
        except Exception:
            LOG.exception(_LE("Failed to initialize driver."),
                          resource={'type': 'driver',
                                    'id': self.__class__.__name__})
            # we don't want to continue since we failed
            # to initialize the driver correctly.
            return
        self.publish_service_capabilities(ctxt)

    # RPC Method
    def get_resource(self, context, migration_ref, resource_ref,
                     dest_host):
        resource_type = resource_ref.type

        if resource_type == 'instance':
            self._get_instance(context, migration_ref, resource_ref,
                               dest_host)
        elif resource_type == 'volume':
            self._get_volume(context, migration_ref, resource_ref,
                             dest_host)
        elif resource_type == 'network':
            self._get_network(context, migration_ref, resource_ref,
                              dest_host)

    def _convert_disks(self, disks):
        LOG.info(_LI('Disk conversion started: %s'), disks)
        converted_disks = []
        for disk in disks:
            index = disk.keys()[0]
            path = disk[index]
            disk[index] = path.replace('.vmdk', '.qcow2')
            utils.convert_image(path, disk[index],
                                'qcow2', run_as_root=True)
            converted_disks.append(disk)
        return converted_disks

    def _get_instance(self, context, migration_ref,
                      resource_ref, dest_host):
        instance_id = resource_ref.id_at_source
        LOG.info(_LI('Getting instance from source hypervisor, '
                     'instance_id: %s'), instance_id)
        migration_ref.save()
        instance_disks = self.driver.get_instance(context, instance_id)
        instance_disks = self._convert_disks(instance_disks)

        instance_info = ast.literal_eval(resource_ref.properties)
        instance_info['disks'] = instance_disks
        _cast_to_destination(context, dest_host, 'create_instance',
                             migration_ref, resource_ref, **instance_info)

    def _get_volume(self, context, migration_ref,
                    resource_ref, dest_host):
        volume_id = resource_ref.id_at_source
        LOG.info(_LI('Getting volume from source hypervisor, '
                     'volume_id: %s'), volume_id)
        migration_ref.migration_status = "Inprogress"
        migration_ref.migration_event = "Fetching from source"
        migration_ref.save()
        volume_path = self.driver.get_volume(context, volume_id,
                                             migration_ref.id)
        volume_info = ast.literal_eval(resource_ref.properties)
        volume_info['path'] = volume_path
        _cast_to_destination(context, dest_host, 'create_volume',
                             migration_ref, resource_ref, **volume_info)

    def _get_network(self, context, migration_ref,
                     resource_ref, dest_host):
        network_info = ast.literal_eval(resource_ref.properties)
        LOG.info(_LI('Getting network information from source hypervisor, '
                     'network_info: %s'), network_info)
        migration_ref.migration_status = "Inprogress"
        migration_ref.migration_event = "Fetching from source"
        migration_ref.save()
        _cast_to_destination(context, dest_host, 'create_network',
                             migration_ref, resource_ref, **network_info)

    @periodic_task.periodic_task
    def _report_driver_status(self, context):
        status = {}
        status["capabilities"] = self.configuration.capabilities.split(',')
        status["free_space"] = _get_free_space(
            self.configuration.conversion_dir)
        resources = {}
        for capab in status["capabilities"]:
            if capab == 'instance':
                instances = self.driver.get_instances_list(context)
                if instances:
                    resources['instance'] = instances
            elif capab == 'volume':
                volumes = self.driver.get_volumes_list(context)
                if volumes:
                    resources['volume'] = volumes
            elif capab == 'network':
                networks = self.driver.get_networks_list(context)
                if networks:
                    resources['network'] = networks
            else:
                LOG.debug("Invalid Capability %s" % (capab))
        status['resources'] = resources
        self.update_service_capabilities(status)

    def publish_service_capabilities(self, context):
        """Collect driver status and then publish."""
        self._report_driver_status(context)
        self._publish_service_capabilities(context)


class DestinationManager(manager.SchedulerDependentManager):
    """Manages destination driver."""

    RPC_API_VERSION = '1.8'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, destination_driver=None, service_name=None,
                 *args, **kwargs):
        """Load the destination driver."""
        # updated_service_capabilities needs service_name to be "source".
        super(DestinationManager, self).__init__(service_name='destination',
                                                 *args, **kwargs)
        self.configuration = config.Configuration(destination_manager_opts,
                                                  config_group=service_name)
        self.stats = {}

        if not destination_driver:
            # Get from configuration, which will get the default
            # if its not using the multi backend.
            destination_driver = self.configuration.destination_driver

        svc_host = utils.extract_host(self.host)
        try:
            objects.Service.get_by_args(context.get_admin_context(),
                                        svc_host, 'guts-destination')
        except exception.ServiceNotFound:
            LOG.info(_LI("Service not found for updating."))

        self.driver = importutils.import_object(
            destination_driver,
            configuration=self.configuration,
            host=self.host)

    def init_host(self):
        """Perform any required initialization."""
        ctxt = context.get_admin_context()

        LOG.info(_LI("Starting destination driver %(driver_name)s."),
                 {'driver_name': self.driver.__class__.__name__})
        try:
            self.driver.do_setup(ctxt)
        except Exception:
            LOG.exception(_LE("Failed to initialize driver."),
                          resource={'type': 'driver',
                                    'id': self.__class__.__name__})
            # we don't want to continue since we failed
            # to initialize the driver correctly.
            return
        self.publish_service_capabilities(ctxt)

    @periodic_task.periodic_task
    def _report_driver_status(self, context):
        status = {}
        status["capabilities"] = self.configuration.capabilities
        con_dir = self.configuration.conversion_dir
        status["free_space"] = _get_free_space(con_dir)
        self.update_service_capabilities(status)

    def publish_service_capabilities(self, context):
        """Collect driver status and then publish."""
        self._report_driver_status(context)
        self._publish_service_capabilities(context)

    def create_network(self, context, **kwargs):
        """Creates new network on destination OpenStack hypervisor."""
        LOG.info(_LI('Create network started, network: %s.'), kwargs['id'])
        del kwargs['id']
        del kwargs['name']
        migration_ref = kwargs.pop('migration_ref')
        resource_ref = kwargs.pop('resource_ref')
        migration_ref.migration_event = 'Creating at destination'
        migration_ref.save()
        try:
            self.driver.create_network(context, **kwargs)
        except exception.NetworkCreationFailed:
            migration_ref.migration_status = 'ERROR'
            migration_ref.migration_event = None
            migration_ref.save()
            raise
        migration_ref.migration_status = 'COMPLETE'
        migration_ref.migration_event = None
        migration_ref.save()
        resource_ref.migrated = True
        resource_ref.save()

    def create_volume(self, context, **kwargs):
        """Creats volume on destination OpenStack hypervisor."""
        LOG.info(_LI('Create volume started, volume: %s.'), kwargs['id'])
        del kwargs['id']
        migration_ref = kwargs.pop('migration_ref')
        resource_ref = kwargs.pop('resource_ref')
        migration_ref.migration_event = 'Creating at destination'
        migration_ref.save()
        kwargs['mig_ref_id'] = migration_ref.id
        try:
            self.driver.create_volume(context, **kwargs)
        except exception.NetworkCreationFailed:
            migration_ref.migration_status = 'ERROR'
            migration_ref.migration_event = None
            migration_ref.save()
            raise
        migration_ref.migration_status = 'COMPLETE'
        migration_ref.migration_event = None
        migration_ref.save()
        resource_ref.migrated = True
        resource_ref.save()

    def create_instance(self, context, **kwargs):
        """Create a new instance."""
        LOG.info(_LI('Create instance started.'))
        migration_ref = kwargs.pop('migration_ref')
        resource_ref = kwargs.pop('resource_ref')
        migration_ref.migration_event = 'Creating at destination'
        migration_ref.save()
        kwargs['mig_ref_id'] = migration_ref.id
        try:
            self.driver.create_instance(context, **kwargs)
        except exception.NetworkCreationFailed:
            migration_ref.migration_status = 'ERROR'
            migration_ref.migration_event = None
            migration_ref.save()
            raise
        migration_ref.migration_status = 'COMPLETE'
        migration_ref.migration_event = None
        migration_ref.save()
        resource_ref.migrated = True
        resource_ref.save()
