
import os
import requests
import subprocess
import time

from oslo_config import cfg

from pyVim import connect
from pyVmomi import vim
from oslo_utils import importutils
from oslo_log import log as logging

from guts.image import glance as image_api
from guts.compute import nova as nova_api
from guts import db

GUTS_DIR = "/tmp/guts"


def _get_service_instance():
        return connect.SmartConnect(
            protocol="https",
            host="192.168.125.35",
            user='administrator@vsphere.local',
            pwd="POIpoi99(",
        )


class MigrationVM(object):

    def __init__(self, uuid, name=None, disks_path=None):
        self.uuid = uuid
        self.name = name
        if disks_path:
            self.disks_path = disks_path
        else:
            self.disks_path = _get_vm_dir(uuid)
        if not os.path.exists(self.disks_path):
            os.makedirs(self.disks_path)
        self._is_converted = False


def _get_vm_dir(uuid):
    return os.path.join(GUTS_DIR, uuid)


class VSphereDriver(object):

    def get_all_vms(self):

    def _fetch_vm_from_hypervisor(self, vm):
        LOG.info('Fetching vm disc from hypervisor')

    def _fetch_vm(self, context, vm):
        self._fetch_vm_from_hypervisor(vm)

    def _convert_vm(self, vm):
        LOG.info('converting vm image to qcow2')
        vmdks = []
        for vm_disks_dir, vm_disks_dirs, files in os.walk(vm.disks_path):
            for file in files:
                if file.endswith('.vmdk'):
                    vmdks.append(file)

        if len(vmdks) == 1:
            vm.target_vm_disk_path = os.path.join(vm.disks_path, "disk-0.qcow2.img")
            subprocess.call(['qemu-img', 'convert',
                             os.path.join(vm.disks_path, 'disk-0.vmdk'),
                             '-ocompat=0.10',
                             '-Oqcow2', vm.target_vm_disk_path])
        vm._is_converted = True

    def _prepare_image_meta(self, vm):
        return {
            'name': vm.name,
            'disk_format': 'qcow2',
            'container_format': 'bare',
        }

    def _push_to_glance(self, context, vm):
        LOG.info('Pushing images to glance')
        image_meta = self._prepare_image_meta(vm)
        glance_client = image_api.GlanceAPI(context)
        image = glance_client.create(context, image_meta)
        image.update(data=open(os.path.join(vm.disks_path, 'disk-0.vmdk'), 'rb'))
        LOG.info('Upload to glance successful')
        return image

    def nova_boot(self, context, image, flavor, vm, *args, **kwargs):
        LOG.info('Booting images to private network')
        nova_client = nova_api.NovaAPI(context)
        server_info = {
            'name': vm.name,
            'image': image.id,
            'flavor': flavor,
            'nics': [{"net-id": '170a2250-ab26-4eb6-9e22-d45de180d473'}]
        }
        return nova_client.boot(context, server_info)

    def create_migration(self, ctxt, migration_id, vm_uuid):
        vm = MigrationVM(vm_uuid)
        migration_ref = db.migration_get(ctxt, migration_id['id'])
        db.migration_update(ctxt, migration_ref.id,
                            dict(migration_event="Fetching_images"))
        #self._fetch_vm(ctxt, vm)
        db.migration_update(ctxt, migration_ref.id,
                            dict(migration_event="Converting_images"))
        #self._convert_vm(vm)
        db.migration_update(ctxt, migration_ref.id,
                            dict(migration_event="Pushing to glance"))
        image = self._push_to_glance(ctxt, vm)
        db.migration_update(ctxt, migration_ref.id,
                            dict(migration_event="Booting images"))
        self.nova_boot(ctxt, image, 3, vm)
        db.migration_update(ctxt, migration_ref.id,
                            dict(migration_event=None))
        LOG.info("Successfully migrated vm %s" % vm.name)


def get_all_vms(context, source_id):
    driver = get_driver(source_id)
    return driver.get_all_vms()

