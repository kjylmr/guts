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

import os

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import importutils

from guts.compute import nova
from guts import db
from guts.image import glance
from guts import manager
from guts import utils

migration_manager_opts = [
    cfg.StrOpt('conversion_dir',
               default='$state_path/migrations',
               help='Disk conversion directory.'),
]

CONF = cfg.CONF
CONF.register_opts(migration_manager_opts)

LOG = logging.getLogger(__name__)

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


class MigrationManager(manager.Manager):
    """Creates & manages VM migrations."""

    RPC_API_VERSION = '1.11'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, service_name=None,
                 *args, **kwargs):
        super(MigrationManager, self).__init__(*args, **kwargs)

    def _prepare_connection_dict(self, con_string):
        con_dict = {}
        for param in con_string.split(';'):
            key = param.split('=')[0]
            value = param.split('=')[1]
            con_dict[key] = value

        return con_dict

    def _get_migration_driver(self, context,
                              source_driver_path, con_string):
        driver_path = importutils.import_module(source_driver_path)
        driver = driver_path.get_migration_driver(context)

        con_dict = self._prepare_connection_dict(con_string)
        driver.initialize(con_dict)
        return driver

    def _get_driver_from_source(self, context, source):
        source_type_id = source.get('source_type_id')
        con_string = source.get('connection_params')
        source_type = db.source_type_get(context, source_type_id)
        source_driver_path = source_type.get('driver_class_path')

        return self._get_migration_driver(context,
                                          source_driver_path,
                                          con_string)

    def fetch_vms(self, context, source_hypervisor_id):
        """Fetch VM list from source hypervisor"""
        if not source_hypervisor_id:
            raise

        source = db.source_get(context, source_hypervisor_id)

        driver = self._get_driver_from_source(context, source)
        vms = driver.get_vms_list()

        db.delete_vms_by_source_id(context, source_hypervisor_id)

        for vm in vms:
            vm['source_id'] = source_hypervisor_id
            db.vm_create(context, vm)

    def _convert_disks(self, context, migration_id, disks):
        self._migration_status_update(context, migration_id,
                                      MIGRATION_EVENT['convert'])
        for disk in disks:
            path = disk['path']
            disk['dest_path'] = path.replace('.vmdk', '.qcow2')
            utils.convert_image(path, disk['dest_path'],
                                'qcow2', run_as_root=False)
            disk['size'] = utils.qemu_img_info(disk['dest_path'],
                                               run_as_root=True).virtual_size

    def _migration_status_update(self, context, id, event=None, status=None):
        data = {}
        if event:
            data['migration_event'] = event
        if status:
            data['migration_status'] = status
        if data:
            db.migration_update(context, id, data)

    def _upload_to_glance(self, context, migration_id, vm_id, disks):
        self._migration_status_update(context, migration_id,
                                      MIGRATION_EVENT['upload'])
        gc = glance.GlanceAPI(context)

        for disk in disks:
            name = "%s-%s" % (vm_id, disk['target_id'].split('.')[0])
            image_meta = {'name': name,
                          'disk_format': 'qcow2',
                          'container_format': 'bare'}
            image = gc.create(image_meta, disk['dest_path'])
            disk['image_id'] = image.id

    def _boot_vm(self, context, migration_id, disks, vm_name):
        self._migration_status_update(context, migration_id,
                                      MIGRATION_EVENT['boot'])
        nc = nova.NovaAPI(context)

        server_id = nc.create(context, disks, vm_name)
        return server_id

    def create_migration(self, context, migration_ref):
        """Creates the migration process of a VM."""
        try:
            vm_id = migration_ref.get('source_instance_id')
            vm = db.vm_get(context, vm_id)
            source = db.source_get(context, vm.get('source_id'))

            migration_id = migration_ref.get('id')
            self._migration_status_update(context, migration_id,
                                          MIGRATION_EVENT['connect'],
                                          MIGRATION_STATUS['init'])

            driver = self._get_driver_from_source(context, source)

            source_vm_id = vm.get('uuid_at_source')

            vm_conversion_dir = os.path.join(CONF.conversion_dir, vm_id)
            utils.execute('mkdir', '-p', vm_conversion_dir,
                          run_as_root = False)

            self._migration_status_update(context, migration_id,
                                          MIGRATION_EVENT['fetch'],
                                          MIGRATION_STATUS['inprogress'])
            disks = driver.download_vm_disks(context, source_vm_id,
                                             vm_conversion_dir)

            self._convert_disks(context, migration_id, disks)

            image_name_prefix = vm.get('name')

            if not image_name_prefix:
                image_name_prefix = vm_id

            self._upload_to_glance(context, migration_id,
                                   image_name_prefix, disks)

            dest_id = self._boot_vm(context, migration_id,
                                    disks, image_name_prefix)

            self._migration_status_update(context, migration_id,
                                          MIGRATION_EVENT['done'],
                                          MIGRATION_STATUS['complete'])

            db.vm_update(context, vm_id, {'migrated': True,
                                          'dest_id': dest_id})
        except Exception:
            self._migration_status_update(context, migration_id,
                                          None, MIGRATION_STATUS['error'])
            raise
