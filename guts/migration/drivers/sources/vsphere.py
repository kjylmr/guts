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

from oslo_config import cfg

from pyVim import connect
from pyVmomi import vim


from guts.migration.drivers import driver

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
    """ VSphere Source Hypervisor"""
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

    def get_instances_list(self):
        instances = get_obj(self.content, [vim.VirtualMachine])

        instance_list = []
        for instance in instances:
            if instance.config.instanceUuid in self.exclude:
                continue;
            inst = {}
            inst["id"] = instance.config.instanceUuid
            inst["name"] = instance.config.name
            inst["memory"] = instance.config.hardware.memoryMB
            inst['vcpus'] = instance.config.hardware.numCPU
            instance_list.append(inst)

        return instance_list

    def get_volumes_list(self):
        raise NotImplemented

    def get_networks_list(self):
        raise NotImplemented
