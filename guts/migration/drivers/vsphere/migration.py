
from oslo_log import log as logging

from guts.migration.common import migration
from guts.migration.drivers.vsphere import client

LOG = logging.getLogger(__name__)


class VSphereMigration(migration.BaseMigration):
    """
    Migration class which is always called to perform complete migration.
    Derived from common `migration.BaseMigration` class.

    Must implement methods
        * `fetch_vm`
        * `convert_vm`

    Attributes:
        * fetch_vm()
        * convert_vm()
        * push_to_glance()
        * boot_image()
    """

    def __init__(self, ctxt, vm, migration_ref, source_hypervisor_id):
        """
        Args:
            ctxt (guts.context.RequestContext): request_context object for
                    authorization.
            vm (guts.migration.common.vm.MigrationVM): Instance of migration VM
            source_hypervisor_id (str): source_hypervisor_id
        """
        self.ctxt = ctxt
        self.vm = vm
        self.migration_ref = migration_ref
        params = client.get_client_params(source_hypervisor_id)
        self.vsphere_client = client.VSphereClient(**params)

    def __call__(self):
        try:
            self.update_migration(migration_status='IN-PROGRESS',
                                  migration_event='INIT')
            self.fetch_vm()
            self.convert_vm()
            image = self.push_to_glance()
            self.boot_image(image.id)
            self.update_migration(migration_status="COMPLETED",
                                  migration_event="COMPLETED")
            LOG.debug("Migration complete")
        except Exception:
            LOG.error('Exception occurred while doing migration')
            self.update_migration(migration_status="FAILED",
                                  migration_event="FAILED")

    def fetch_vm(self):
        self.update_migration(migration_event="FETCHING_IMAGES")
        self.vsphere_client.fetch_vm(self.vm)

    def convert_vm(self):
        self.update_migration(migration_event="CONVERTING_IMAGES")
        self.vm.convert()
