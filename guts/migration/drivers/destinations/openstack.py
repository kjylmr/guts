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

import ast
import time

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

openstack_destination_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v2.0',
               help='Identity service endpoint for authorization'),
    cfg.StrOpt('username',
               help='Name used for authentication with the '
                    'OpenStack Identity service.'),
    cfg.StrOpt('password',
               help='Password used for authentication with the OpenStack '
                    'Identity service.'),
    cfg.StrOpt('tenant_name',
               help='Tenant to request authorization on.'),
    cfg.StrOpt('project_id',
               help='Project ID for project scoping.'),
    cfg.StrOpt('user_domain_name',
               help="User's domain ID for authentication"),
    cfg.StrOpt('keystone_version',
               default='v2',
               choices=['v2', 'v3'],
               help="User's domain ID for authentication"),
    cfg.StrOpt('nova_api_version',
               default='2',
               help='Shows the client version.'),
    cfg.StrOpt('cinder_api_version',
               default='2',
               help='Cinder client version.'),
    cfg.StrOpt('glance_api_version',
               default='1',
               help='Glance client version.'),
]

LOG = logging.getLogger(__name__)


class OpenStackDestinationDriver(driver.DestinationDriver):
    """OpenStack Destination Hypervisor"""
    def __init__(self, *args, **kwargs):
        super(OpenStackDestinationDriver, self).__init__(*args, **kwargs)

    def get_credentials(self):
        self.configuration.append_config_values(openstack_destination_opts)
        return {'auth_url': self.configuration.auth_url,
                'username': self.configuration.username,
                'password': self.configuration.password,
                'tenant_name': self.configuration.tenant_name,
                'project_id': self.configuration.project_id,
                'user_domain_name': self.configuration.user_domain_name,
                'nova_api_version': self.configuration.nova_api_version,
                'cinder_api_version': self.configuration.cinder_api_version,
                'glance_api_version': self.configuration.glance_api_version,
                'keystone_version': self.configuration.keystone_version}

    def do_setup(self, context):
        """Any initialization the source driver does while starting."""
        self.creds = ast.literal_eval(self.hypervisor_ref.credentials)
        auth_url = self.creds['auth_url']
        if auth_url is None:
            raise ValueError(_("Cannot authenticate without an auth_url"))
        username = self.creds['username']
        password = self.creds['password']
        tenant_name = self.creds['tenant_name']
        project_id = self.creds['project_id']
        user_domain_name = self.creds['user_domain_name']
        nova_api_version = self.creds['nova_api_version']
        cinder_api_version = self.creds['cinder_api_version']
        glance_api_version = self.creds['glance_api_version']
        keystone_version = self.creds['keystone_version']

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

    def create_network(self, context, **kwargs):
        if not self._initialized:
            self.do_setup(context)
        try:
            self.nova.networks.create(**kwargs)
        except Exception as e:
            LOG.error(_LE("Failed to create network '%s' on "
                          "destination: %s"), kwargs['label'], e)
            raise exception.NetworkCreationFailed(reason=e.message)

    def get_keypairs_list(self):
        if not self._initialized:
            self.do_setup(context)
        keypairs = self.nova.keypairs.list()
        keypair_list = []
        for k in keypairs:
            keypair_list.append(k.name)
        return keypair_list

    def get_secgroups_list(self):
        if not self._initialized:
            self.do_setup(context)
        secgroups = self.nova.security_groups.list()
        secgroups_list = []
        for s  in secgroups:
            secgroups_list.append(s.name)
        return secgroups_list

    def get_networks_list(self):
        if not self._initialized:
            self.do_setup(context)
        networks = self.nova.networks.list()
        net_list = []
        for n in networks:
            net_list.append(n.label)
        return net_list

    def create_volume(self, context, **kwargs):
        if not self._initialized:
            self.do_setup(context)
        image_name = kwargs['mig_ref_id']
        try:
            self._upload_image_to_glance(image_name, kwargs['path'])
            utils.execute('rm', kwargs['path'], run_as_root=True)
            img = self.glance.images.find(name=image_name)
            if img.status != 'active':
                raise Exception
            vol = self.cinder.volumes.create(name=kwargs['name'],
                                             size=int(kwargs['size']),
                                             imageRef=img.id)
            while vol.status != 'available':
                time.sleep(5)
                vol = self.cinder.volumes.get(vol.id)
            self.glance.images.delete(img.id)
        except Exception as e:
            LOG.error(_LE('Failed to create volume from image at destination '
                          'image_name: %s %s'), image_name, e)
            raise exception.VolumeCreationFailed(reason=e.message)

    def _upload_image_to_glance(self, image_name, file_path):
        out, err = utils.execute('glance', '--os-username',
                                 self.creds['username'],
                                 '--os-password', self.creds['password'],
                                 '--os-tenant-name',
                                 self.creds['tenant_name'],
                                 '--os-auth-url', self.creds['auth_url'],
                                 'image-create', '--file', file_path,
                                 '--disk-format', 'raw', '--container-format',
                                 'bare', '--name', image_name,
                                 run_as_root=True)

    def nova_boot(self, instance_name, image_name, extra_params):
        if extra_params:
            extra_params = ast.literal_eval(extra_params)
        flavor = extra_params.get('flavor', 2)
        network = extra_params.get('network', None)
        sec_group = extra_params.get('secgroup', None)
        keypair = extra_params.get('keypair', None)
        boot_string = ['nova', '--os-username', self.crds['username'],
                       '--os-password', self.creds['password'],
                       '--os-tenant-name', self.creds['tenant_name'],
                       '--os-auth-url', self.creds['auth_url'],
                       'boot', '--image', image_name,
                       '--flavor', flavor,
                       instance_name]
        if network:
            boot_string.extend(['--nic', "net-id=%s" % (network)])
        if keypair:
            boot_string.extend(['--key-name', keypair])
        if sec_group:
            boot_string.extend(['--security-groups', secgroup])
        out, err = utils.execute(*boot_string, run_as_root=True)

    def create_instance(self, context, extra_params=None, **kwargs):
        disks = kwargs['disks']
        mig_ref = kwargs['mig_ref_id']
        count = 0

        for disk in disks:
            image_name = "%s_%s" % (mig_ref, count)
            self._upload_image_to_glance(image_name, disk[str(count)])
            if count == 0:
                self.nova_boot(kwargs['name'], image_name, extra_params)
            else:
                img = self.glance.images.find(name=image_name)
                self.cinder.volumes.create(
                    display_name="%s_vol" % kwargs['name'],
                    size=8,
                    imageRef=img.id)
            count += 1
