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


from guts.migration.drivers import driver
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client as n_client
from cinderclient import client
from oslo_config import cfg


openstack_source_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v2.0',
               help='	'),
    cfg.StrOpt('username',
               default='admin',
               help='Name used for authentication with the OpenStack Identity service.'),
    cfg.StrOpt('password',
               default='password',
               help='Password used for authentication with the OpenStack Identity service.'),
    cfg.StrOpt('tenant_name',
               default='admin',
               help='Tenant to request authorization on.'),
    cfg.StrOpt('nova_api_version',
               default='2',
               help='Shows the client version.'),
    cfg.StrOpt('cinder_api_version',
               default='1',
               help='File with the list of available gluster shares'),
]

CONF = cfg.CONF
CONF.register_opts(openstack_source_opts)


class OpenStackSourceDriver(driver.SourceDriver):
    """ OpenStack Source Hypervisor"""
    def __init__(self, *args, **kwargs):
        super(OpenStackSourceDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(openstack_source_opts)

    def do_setup(self, context):
        """Any initialization the source driver does while starting."""
        super(OpenStackSourceDriver, self).do_setup(context)
        auth_url = self.configuration.auth_url
        username = self.configuration.username
        password = self.configuration.password
        tenant_name = self.configuration.tenant_name
        nova_api_version = self.configuration.nova_api_version
        cinder_api_version = self.configuration.cinder_api_version

        auth = v2.Password(auth_url, username=username, password=password, tenant_name=tenant_name)
        sess = session.Session(auth=auth)
        self.nova  = n_client.Client(nova_api_version, session=sess)
        self.cinder  = client.Client(cinder_api_version, session=sess)

    def get_instances_list(self):
        instances = self.nova.servers.list()
        return instances

    def get_volumes_list(self):
        src_volumes = self.cinder.volumes.list()
        volumes = []
        for vol in src_volumes:
            v = {'name': vol.display_name,
                 'id': vol.id,
                 'size': vol.size
            }
            volumes.append(v)
        return volumes

    def get_networks_list(self):
        src_networks = self.nova.networks.list()
        networks = []
        for network in src_networks:
            net = {'bridge': network.bridge,
                   'dhcp_start': network.dhcp_start,
                   'id': network.id,
                   'gateway': network.gateway,
                   'name': network.label,
                   'broadcast': network.broadcast,
                   'netmask': network.netmask,
                   'cidr': network.cidr,
                   'enable_dhcp': network.enable_dhcp,
                   'dhcp_server': network.dhcp_server,
                   'dns': network.dns1
            }
            networks.append(net)

        return networks
