
import requests
import os
import time
import threading

from oslo_log import log as logging
from oslo_config import cfg
from pyVim import connect
from pyVmomi import vim
from urlparse import urlparse

LOG = logging.getLogger(__name__)

CHUNK_SIZE = 512*1024

# TODO: Remove these options once MigrationManager.get_driver is implemented
migration_driver_opts = [
    cfg.StrOpt('migration_driver',
               default='guts.migration.drivers',
               help='Default driver to use for migration'),
    cfg.StrOpt('GUTS1_user',
               default='root',
               help='Default user to login to hypervisor'),
    cfg.StrOpt('GUTS1_pwd',
               default='',
               help='Password to login to hypervisor'),
    cfg.StrOpt('GUTS1_host',
               default='',
               help='hostname of hypervisor instance')
]

CONF = cfg.CONF
CONF.register_opts(migration_driver_opts)


class VSphereClient(object):
    """
    A wrapper client class to provide functionality for VSphere interaction

    Attributes:
        * fetch_vm (vm_uuid, destination_path):
            Fetches vm specified by vm_uuid from VSphere cloud and stores to
            destination_path

        * get_all_vms():
            returns a list of vms within given VSphere cloud
    """

    def __init__(self, host, protocol='https', user=None, pwd=None):
        """
        Args:
            host (str): VSphere host string without protocol. eg: "192.168.12.34"
            protocol (str): protocol of the host
            user (str): username of VSphere instance
            pwd (str): password of VSphere instance
        """
        self._service_instance = connect.SmartConnect(protocol=protocol,
                                                      host=host, user=user,
                                                      pwd=pwd)
        self._content = self._service_instance.content

    def fetch_vm(self, vm):
        """
        Fetches vm specified by vm_uuid from VSphere cloud and stores to
        provided destination_path

        Args:
            vm_uuid: uuid of the vm.
            destination_path: Path where vm will be stored after fetching

        Returns:
            None

        Exceptions:

        """
        vmw_vm = self._get_by_id(vm.uuid)
        vm.name = vmw_vm.name
        lease = self._get_vm_lease(vmw_vm)

        def keep_lease_alive(lease):
            count = 0
            while True:
                time.sleep(5)
                count += 1
                try:
                    if lease.state == vim.HttpNfcLease.State.ready and count == 12:
                        LOG.debug("Migration still active, renewing lease")
                        lease.HttpNfcLeaseProgress(50)
                        count = 0
                    elif lease.state in [vim.HttpNfcLease.State.done,
                                         vim.HttpNfcLease.State.error]:
                        return
                except:
                    LOG.debug("exception occurred during keeping lease alive")
                    return

        try:
            device_urls = self._get_device_urls(lease)

            if lease.state == vim.HttpNfcLease.State.ready:
                keepalive_thread = threading.Thread(
                                                    target=keep_lease_alive,
                                                    args=(lease,))
                keepalive_thread.daemon = True
                keepalive_thread.start()
                for device_url in device_urls:
                    vm.vm_disks.append(device_url.targetId)
#                     vm.source_disks_path.append(device_url.targetId)
                    current_disk_path = os.path.join(vm.base_path,
                                                     device_url.targetId)
                    if os.path.exists(current_disk_path):
                        msg = "Skipping fetch of %s" % device_url.targetId
                        LOG.debug(msg)
                        continue
                    LOG.debug("Fetching %s" % device_url.url)
                    url = device_url.url
                    r = requests.get(url, verify=False)
                    f = open(current_disk_path, "wb")
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                    f.close()
                self._mark_lease_complete(lease)
                keepalive_thread.join()
            elif lease.state == vim.HttpNfcLease.State.error:
                # TODO: Raise approp exception
                raise Exception
        except Exception:
            #HttpNfcLeaseAbort
            raise Exception

    @staticmethod
    def _get_device_urls(lease):
        try:
            device_urls = lease.info.deviceUrl
        except IndexError:
            time.sleep(2)
            device_urls = lease.info.deviceUrl
        return device_urls

    def _get_by_id(self, uuid):
        return self._content.searchIndex.FindByUuid(None, uuid, True, True)

    @staticmethod
    def _get_vm_lease(vm):
        # TODO: Raise exec for the case when VM is not shutdown
        lease = vm.ExportVm()
        if lease.state != 'ready':
            # TODO: clean old lease if this is a very frequent request
            time.sleep(5)
            lease = vm.ExportVm()
            #raise Exception("Couldn't get lease")
        return lease

    @staticmethod
    def _mark_lease_complete(lease):
        lease.HttpNfcLeaseComplete()

    def get_all_vms(self):
        """
        Returns a list of vms within given VSphere cloud

        Returns:
            A list of dict containing following keys
            ('name', 'guest_id', 'vmPathName', 'uuid')

        Exceptions:

        """
        vm_container_view = self._content.viewManager.CreateContainerView(
                            self._content.rootFolder,
                            [vim.VirtualMachine],
                            True)
        vms = vm_container_view.view
        vms_info = []
        for vm in vms:
            uuid = vm.summary.config.instanceUuid
            vm_info = {
                'name': vm.name,
                'guest_id': vm.summary.config.guestId,
                'vmPathName': vm.summary.config.vmPathName,
                'uuid': uuid
            }
            vms_info.append(vm_info)
        return vms_info


def get_client_params(source_hypervisor_id):
    """
    Prepares a dict of auth params from source_hypervisor_id. Fetches db and
    gets corresponding auth credentials

    Args:
        source_hypervisor_id (str): source_hypvervisor_id

    Returns:
        {}

    Exceptions:

    """
    parsed_uri = urlparse(CONF.GUTS1_host)
    return {'host': parsed_uri.netloc,
            'protocol': parsed_uri.scheme,
            'user': CONF.GUTS1_user,
            'pwd': CONF.GUTS1_pwd}
