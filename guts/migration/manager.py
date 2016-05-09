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

import functools
import os

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import importutils
from oslo_service import periodic_task

from guts.compute import nova
from guts import context
from guts import db
from guts import exception
from guts.i18n import _, _LW, _LE, _LI
from guts.image import glance
from guts import manager
from guts import objects
from guts import rpc
from guts import utils
from guts.migration import configuration as config


source_manager_opts = [
    cfg.StrOpt('source_driver',
               default='guts.migration.source_drivers.vmware.VSphere',
               help='Driver to use for source hypervisor'),
    cfg.StrOpt('conversion_dir',
               default='$state_path/migrations',
               help='Disk conversion directory.'),
    cfg.StrOpt('capabilities',
               default='instance',
               help='Specifies types of migrations this driver supports.'),
]

destination_manager_opts = [
    cfg.StrOpt('destination_driver',
               default='guts.migration.destination_drivers.openstack.OpenStack',
               help='Driver to use for destination hypervisor'),
    cfg.StrOpt('conversion_dir',
               default='$state_path/migrations',
               help='Disk conversion directory.'),
    cfg.StrOpt('capabilities',
               default='instance',
               help='Specifies types of migrations this driver supports.'),
]

CONF = cfg.CONF
CONF.register_opts(source_manager_opts)
CONF.register_opts(destination_manager_opts)

LOG = logging.getLogger(__name__)

get_notifier = functools.partial(rpc.get_notifier, service='migration')
wrap_exception = functools.partial(exception.wrap_exception,
                                   get_notifier=get_notifier)

MIGRATION_STATUS = {'init': 'Initiating',
                    'inprogress': 'Inprogress',
                    'complete': 'Completed',
                    'error': 'Error'}

MIGRATION_EVENT = {'connect': 'Connecting to VM',
                   'fetch': 'Fetching VM Disk(s)',
                   'convert': 'Converting VM Disk(s)',
                   'upload': 'Uploading to Glance',
                   'boot': 'Booting Instance',
                   'done': '-'}

def _get_free_space(conversion_dir):
    """Calculate and return free space available."""
    out, _ = utils.execute('df', '--portability', '--block-size', '1',
                           conversion_dir,
                           run_as_root=True)
    out = out.splitlines()[1]
    available = int(out.split()[3])

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
            service = objects.Service.get_by_args(context.get_admin_context(),
                                                  svc_host, 'guts-source')
        except exception.ServiceNotFound:
            LOG.info(_LI("Service not found for updating."))

    @periodic_task.periodic_task
    def _report_driver_status(self, context):
        status = {}
        status["capabilities"] = self.configuration.capabilities
        status["free_space"] = _get_free_space(self.configuration.conversion_dir)
        # Add VMs list to the status.
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
            destination = self.configuration.destination_driver
            
        svc_host = utils.extract_host(self.host)
        try:
            service = objects.Service.get_by_args(context.get_admin_context(),
                                                  svc_host, 'guts-destination')
        except exception.ServiceNotFound:
            LOG.info(_LI("Service not found for updating."))

    @periodic_task.periodic_task
    def _report_driver_status(self, context):
        status = {}
        status["capabilities"] = self.configuration.capabilities
        status["free_space"] = _get_free_space(self.configuration.conversion_dir)
        self.update_service_capabilities(status)

    def publish_service_capabilities(self, context):
        """Collect driver status and then publish."""
        self._report_driver_status(context)
        self._publish_service_capabilities(context)