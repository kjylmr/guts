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


import atexit
import os
import time

from oslo_config import cfg

from pyVim import connect
from pyVmomi import vim
from threading import Thread

from guts.migration.drivers import driver
from guts import utils

vsphere_source_opts = [
    cfg.StrOpt('vsphere_host',
               default='127.0.0.1',
               help='Host name/IP of VSphere server'),
    cfg.StrOpt('vsphere_username',
               default=None,
               help='Username of VShpere server'),
    cfg.StrOpt('vsphere_password',
               default=None,
               help='Password of VShpere server'),
    cfg.StrOpt('vsphere_port',
               default='443',
               help='Port to connect to VShpere server'),
]

CONF = cfg.CONF
CONF.register_opts(vsphere_source_opts)


def get_obj(content, vimtype):
    """Get VIMType Object.

       Return an object by name, if name is None the
       first found object is returned
    """
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    return container.view


class VSphereSourceDriver(driver.SourceDriver):
    """VSphere Source Hypervisor"""
    def __init__(self, *args, **kwargs):
        super(VSphereSourceDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(vsphere_source_opts)

    def do_setup(self, context):
        """Any initialization the source driver does while starting."""
        super(VSphereSourceDriver, self).do_setup(context)
        host = self.configuration.vsphere_host
        username = self.configuration.vsphere_username
        password = self.configuration.vsphere_password
        port = self.configuration.vsphere_port
        try:
            self.con = connect.SmartConnect(host=host, user=username,
                                            pwd=password, port=port)
            atexit.register(connect.Disconnect, self.con)
            self.content = self.con.RetrieveContent()
        except Exception:
            raise
        self._initialized = True

    def get_instances_list(self, context):
        if not self._initialized:
            self.do_setup(context)

        instances = get_obj(self.content, [vim.VirtualMachine])

        instance_list = []
        for instance in instances:
            if instance.config.instanceUuid in self.exclude:
                continue
            inst = {}
            inst["id"] = instance.config.instanceUuid
            inst["name"] = instance.config.name
            inst["memory"] = instance.config.hardware.memoryMB
            inst['vcpus'] = instance.config.hardware.numCPU
            vm_disks = []
            for vm_hardware in instance.config.hardware.device:
                if (vm_hardware.key >= 2000) and (vm_hardware.key < 3000):
                    vm_disks.append('{}'.format(vm_hardware.capacityInKB/1024/1024))

            disks = ','.join(vm_disks)
            inst["root_gb"] = vm_disks[0]
            instance_list.append(inst)

        return instance_list

    def get_volumes_list(self, context):
        raise NotImplementedError()

    def get_networks_list(self, context):
        if not self._initialized:
            self.do_setup(context)

        networks = get_obj(self.content, [vim.Network])

        network_list = []
        for network in networks:
            if network.summary.name in self.exclude:
                continue
            net = {'id': network.name,
                   'name': network.name,
                   'ip_pool': network.summary.ipPoolName,
                   'ip_pool_id': network.summary.ipPoolId}
            network_list.append(net)
        return network_list

    def _find_instance_by_uuid(self, instance_uuid):
        search_index = self.content.searchIndex
        instance = search_index.FindByUuid(None, instance_uuid,
                                           True, True)

        if instance is None:
            raise Exception
        return instance

    def _get_instance_lease(self, instance):
        lease = instance.ExportVm()
        count = 0
        while lease.state != 'ready':
            if count == 5:
                raise Exception("Unable to take lease on sorce instance.")
            time.sleep(5)
            count += 1
        return lease

    def _get_device_urls(self, lease):
        try:
            device_urls = lease.info.deviceUrl
        except IndexError:
            time.sleep(2)
            device_urls = lease.info.deviceUrl
        return device_urls

    def _get_instance_disk(self, device_url, dest_disk_path):
        url = device_url.url
        if not os.path.exists(dest_disk_path):
            utils.execute('wget', url, '--no-check-certificate',
                          '-O', dest_disk_path, run_as_root=True)

    def get_instance(self, context, instance_id):
        instance = self._find_instance_by_uuid(instance_id)
        lease = self._get_instance_lease(instance)

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
                    path = os.path.join(self.configuration.conversion_dir,
                                        device_url.targetId)
                    self._get_instance_disk(device_url, path)
                    data = {device_url.key.split(':')[1]: path}
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
