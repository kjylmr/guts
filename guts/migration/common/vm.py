
import subprocess
import os

from oslo_log import log as logging


LOG = logging.getLogger(__name__)

GUTS_MIGRATION_DIR = "/tmp/guts"


def create_migration_vm_instance(vm_uuid):
    return MigrationVM(vm_uuid)


class MigrationVM(object):
    """

    """

    def __init__(self, uuid):
        self.uuid = uuid
        self._name = None  # str
        self.source_hypervisor_type = None  # str
        self.destination_hypervisor_type = None  # str

        self.base_path = os.path.join(GUTS_MIGRATION_DIR, self.uuid)
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)

        self.vm_disks = []  # list

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def _prepare_image_meta(self):
        return {
            'name': self.name,
            'disk_format': 'qcow2',
            'container_format': 'bare',
        }

    @property
    def target_disk_path(self):
        if not self.name:
            return None
        return os.path.join(self.base_path, "%s.%s" % (self.name, "qcow2"))

    @property
    def source_disk_path(self):
        if not self.vm_disks:
            return None
        return os.path.join(self.base_path, self.vm_disks[0])

    def convert(self):
        if os.path.exists(self.target_disk_path):
            LOG.debug("Converted image already exists, skipping conversion")
        else:
            LOG.debug("Converting vm to %s" % self.target_disk_path)
            subprocess.call(['qemu-img', 'convert',
                             self.source_disk_path,
                             '-ocompat=0.10',
                             '-Oqcow2',
                             self.target_disk_path])
