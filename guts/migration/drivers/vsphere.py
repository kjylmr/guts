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
VSphere based guts driver.
"""

import atexit
import os
import requests
import time

from pyVim import connect
from pyVmomi import vim
from threading import Thread

from guts.migration import driver
from guts import utils

CHUNK_SIZE = 512 * 1024


def get_obj(content, vimtype):
    """Get VIMType Object.

       Return an object by name, if name is None the
       first found object is returned
    """
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    return container.view


class VSphereDriver(driver.MigrationDriver):
    """VSphere (VMWare) Guts driver."""

    def __init__(self, context):
        super(VSphereDriver, self).__init__()
        self.context = context

    def initialize(self, connection_dict):
        try:
            self.con = connect.SmartConnect(host=connection_dict['host'],
                                            user=connection_dict['user'],
                                            pwd=connection_dict['password'],
                                            port=int(connection_dict['port']))
            atexit.register(connect.Disconnect, self.con)
            self.content = self.con.RetrieveContent()
        except Exception:
            raise

    def get_vms_list(self):
        """Get list of VMs available in source hypervisor."""
        if not self.con:
            self.initialize()

        vms = get_obj(self.content, [vim.VirtualMachine])

        vms_list = []
        for vm in vms:
            vm_dict = {}
            vm_dict["uuid_at_source"] = vm.config.instanceUuid
            vm_dict["name"] = vm.config.name
            vms_list.append(vm_dict)

        return vms_list

    def _find_vm_by_uuid(self, vm_uuid):
        search_index = self.content.searchIndex
        vm = search_index.FindByUuid(None, vm_uuid, True, True)

        if vm is None:
            raise Exception
        return vm

    def _get_vm_disk(self, device_url, dest_disk_path):
        url = device_url.url
        r = requests.get(url, verify=False)
        if os.path.exists(dest_disk_path):
            utils.execute('rm', dest_disk_path)
        f = open(dest_disk_path, "wb")
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
        f.close()

    def _get_device_urls(self, lease):
        try:
            device_urls = lease.info.deviceUrl
        except IndexError:
            time.sleep(2)
            device_urls = lease.info.deviceUrl
        return device_urls

    def _get_vm_lease(self, vm):
        lease = vm.ExportVm()
        count = 0
        while lease.state != 'ready':
            if count == 5:
                raise Exception("Unable to take lease on sorce VM.")
            time.sleep(5)
            count += 1
        return lease

    def download_vm_disks(self, context, vm_uuid, base_path):
        vm = self._find_vm_by_uuid(vm_uuid)
        lease = self._get_vm_lease(vm)

        def keep_lease_alive(lease):
            """Keeps the lease alive while GETing the VMDK."""
            while(True):
                time.sleep(5)
                try:
                    # Choosing arbitrary percentage to keep the lease alive.
                    lease.HttpNfcLeaseProgress(50)
                    if (lease.state == vim.HttpNfcLease.State.done):
                        return
                    # If the lease is released, we get an exception.
                    # Returning to kill the thread.
                except Exception:
                    return
        disks = []
        try:
            if lease.state == vim.HttpNfcLease.State.ready:
                keepalive_thread = Thread(target=keep_lease_alive,
                                          args=(lease,))

                keepalive_thread.daemon = True
                keepalive_thread.start()

                device_urls = self._get_device_urls(lease)

                for device_url in device_urls:
                    data = {}
                    path = os.path.join(base_path, device_url.targetId)
                    self._get_vm_disk(device_url, path)
                    data = {'target_id': device_url.targetId,
                            'path': path,
                            'index': device_url.key.split(':')[1],
                            'type': 'vmdk'}
                    disks.append(data)

                lease.HttpNfcLeaseComplete()
                keepalive_thread.join()
            elif lease.state == vim.HttpNfcLease.State.error:
                raise Exception
            else:
                raise Exception
        except Exception:
            raise
        return disks


def get_migration_driver(context):
    return VSphereDriver(context)
