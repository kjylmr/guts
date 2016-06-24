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


import os

from cinderclient import client as cinder_client
from glanceclient import client as glance_client
from guts import exception
from guts.i18n import _, _LE
from guts.migration.drivers import driver
from guts import utils
from keystoneauth1.identity import v3
from keystoneauth1 import session as v3_session
from keystoneclient.auth.identity import v2
from keystoneclient import session as v2_session
from novaclient import client as nova_client

from oslo_config import cfg
from oslo_log import log as logging


openstack_source_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v2.0',
               help='Identity service endpoint for authorization'),
    cfg.StrOpt('username',
               default='admin',
               help='Name used for authentication with the '
                    'OpenStack Identity service.'),
    cfg.StrOpt('password',
               default='password',
               help='Password used for authentication with '
                    'the OpenStack Identity service.'),
    cfg.StrOpt('tenant_name',
               default='admin',
               help='Tenant to request authorization on.'),
    cfg.StrOpt('project_id',
               default='',
               help='Project ID for project scoping.'),
    cfg.StrOpt('user_domain_name',
               default='Default',
               help="User's domain ID for authentication"),
    cfg.StrOpt('keystone_version',
               default='v2',
               help="User's domain ID for authentication"),
]

LOG = logging.getLogger(__name__)


class OpenStackSourceDriver(driver.SourceDriver):
    """OpenStack Source Hypervisor"""
    def __init__(self, *args, **kwargs):
        super(OpenStackSourceDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(openstack_source_opts)

    def do_setup(self, context):
        """Any initialization the source driver does while starting."""
        super(OpenStackSourceDriver, self).do_setup(context)

        auth_url = self.configuration.auth_url
        if auth_url is None:
            raise ValueError(_("Cannot authenticate without an auth_url"))
        username = self.configuration.username
        password = self.configuration.password
        tenant_name = self.configuration.tenant_name
        project_id = self.configuration.project_id
        user_domain_name = self.configuration.user_domain_name
        nova_api_version = self.configuration.nova_api_version
        cinder_api_version = self.configuration.cinder_api_version
        glance_api_version = self.configuration.glance_api_version
        keystone_version = self.configuration.keystone_version

        if keystone_version == 'v3':
            auth = v3.Password(auth_url=auth_url, username=username,
                               password=password, project_id=project_id,
                               user_domain_name=user_domain_name)
            sess = v3_session.Session(auth=auth)
        elif keystone_version == 'v2':
            auth = v2.Password(auth_url, username=username,
                               password=password, tenant_name=tenant_name)
            sess = v2_session.Session(auth=auth)

        self.nova = nova_client.Client(nova_api_version, session=sess)
        self.cinder = cinder_client.Client(cinder_api_version, session=sess)
        self.glance = glance_client.Client(glance_api_version, session=sess)
        self._initialized = True

    def get_instances_list(self, context):
        if not self._initialized:
            self.do_setup(context)
        src_instances = self.nova.servers.list()
        instances = []
        for inst in src_instances:
            if inst.id in self.exclude:
                continue
            flavor_id = inst.flavor.get('id')
            flavor = self.nova.flavors.find(id=flavor_id)
            i = {'name': inst.name,
                 'id': inst.id,
                 'status': inst.status,
                 'memory': flavor.ram,
                 'vcpus': flavor.vcpus,
                 'root_gb': flavor.disk}
            instances.append(i)
        return instances

    def get_volumes_list(self, context):
        if not self._initialized:
            self.do_setup(context)
        src_volumes = self.cinder.volumes.list()
        volumes = []
        for vol in src_volumes:
            if vol.id in self.exclude:
                continue
            v = {'name': vol.display_name,
                 'id': vol.id,
                 'size': vol.size}
            volumes.append(v)
        return volumes

    def get_networks_list(self, context):
        if not self._initialized:
            self.do_setup(context)
        src_networks = self.nova.networks.list()
        networks = []
        for network in src_networks:
            if network.id in self.exclude:
                continue
            net = {'id': network.id,
                   'name': network.label,
                   'bridge': network.bridge,
                   'gateway': network.gateway,
                   'label': network.label,
                   'cidr': network.cidr,
                   'enable_dhcp': network.enable_dhcp,
                   'dhcp_server': network.dhcp_server,
                   'dns1': network.dns1}
            networks.append(net)

        return networks

    def get_instance(self, context, instance_id):
        """Downloads given instance to local conversion directory."""
        if not self._initialized:
            self.do_setup()
        try:
            instance = self.nova.servers.get(instance_id)
            image_id = instance.create_image(instance_id)
            img = self.glance.images.get(image_id)
            while img.status != 'active':
                img = self.glance.images.get(image_id)
            image_path = os.path.join(self.configuration.conversion_dir,
                                      image_id)
            self._download_image_from_glance(image_id, image_path)
            self.glance.images.delete(image_id)
        except Exception as e:
            LOG.error(_LE('Failed to download instance image from source, '
                          'image_id: %s, %s'), image_id, e)
            raise exception.InstanceImageDownloadFailed(reason=e.message)
        return [{'0': image_path}]

    def get_network(self, context, network_id):
        """Get Network information from source hypervisor.

           As network migration is just an local migration, we don't need
           anything from source hypervisor. Required network information
           already stored in guts database.
        """
        pass

    def get_volume(self, context, volume_id, migration_ref_id):
        """Downloads given volume to local conversion directory."""
        if not self._initialized:
            self.do_setup()
        try:
            vol = self.cinder.volumes.get(volume_id)
            status = self.cinder.volumes.upload_to_image(vol, True,
                                                         migration_ref_id,
                                                         'bare', 'raw')
            img_id = status[1]['os-volume_upload_image']['image_id']
            vol_img = self.glance.images.get(img_id)
            while vol_img.status != 'active':
                vol_img = self.glance.images.get(img_id)
            image_path = os.path.join(self.configuration.conversion_dir,
                                      migration_ref_id)
            self._download_image_from_glance(vol_img.id, image_path)
            self.glance.images.delete(vol_img.id)
        except Exception as e:
            LOG.error(_LE('Failed to download volume from source, id: %s, '
                          '%s'), volume_id, e)
            raise exception.VolumeDownloadFailed(reason=e.message)
        return image_path

    def _download_image_from_glance(self, image_id, file_path):
            out, err = utils.execute(
                'glance', '--os-username', self.configuration.username,
                '--os-password', self.configuration.password,
                '--os-tenant-name', self.configuration.tenant_name,
                '--os-auth-url', self.configuration.auth_url,
                'image-download', '--file', file_path,
                image_id, run_as_root=True)
