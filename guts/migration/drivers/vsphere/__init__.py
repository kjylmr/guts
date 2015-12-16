
from guts.migration.common import vm
from guts.migration.drivers.vsphere.migration import VSphereMigration
from guts import db


def create_migration(ctxt, migration_info, vm_uuid,
                     source_hypervisor_id):

    migration_ref = db.migration_get(ctxt, migration_info['id'])
    vm_instance = vm.create_migration_vm_instance(vm_uuid)
    VSphereMigration(ctxt, vm_instance, migration_ref, source_hypervisor_id)()


def get_all_vms(ctxt, source_hypervisor_id):
    pass
