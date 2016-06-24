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
]

LOG = logging.getLogger(__name__)


class OpenStackDestinationDriver(driver.DestinationDriver):
    """OpenStack Destination Hypervisor"""
    def __init__(self, *args, **kwargs):
        super(OpenStackDestinationDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(openstack_destination_opts)

    def do_setup(self, context):
        """Any initialization the destination driver does while starting."""
        super(OpenStackDestinationDriver, self).do_setup(context)
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

    def create_network(self, context, **kwargs):
        if not self._initialized:
            self.do_setup(context)
        try:
            self.nova.networks.create(**kwargs)
        except Exception as e:
            LOG.error(_LE("Failed to create network '%s' on "
                          "destination: %s"), kwargs['label'], e) 
            raise exception.NetworkCreationFailed(reason=e.message)

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
            vol = self.cinder.volumes.create(display_name=kwargs['name'],
                                             size=int(kwargs['size']),
                                             imageRef=img.id)
            while vol.status != 'available':
                vol = self.cinder.volumes.get(vol.id)
            self.glance.images.delete(img.id)
        except Exception as e:
            LOG.error(_LE('Failed to create volume from image at destination '
                          'image_name: %s %s'), image_name, e)
            raise exception.VolumeCreationFailed(reason=e.message)

    def _upload_image_to_glance(self, image_name, file_path):
        out, err = utils.execute('glance', '--os-username',
                                 self.configuration.username,
                                 '--os-password', self.configuration.password,
                                 '--os-tenant-name',
                                 self.configuration.tenant_name,
                                 '--os-auth-url', self.configuration.auth_url,
                                 'image-create', '--file', file_path,
                                 '--disk-format', 'raw', '--container-format',
                                 'bare', '--name', image_name,
                                 run_as_root=True)

    def _flavor_create(self, name, memory, cpus, root_gb):
        flavor = self.nova.flavors.create(name, memory, cpus, root_gb)
        return flavor

    def create_instance(self, context, **kwargs):
        disks = kwargs['disks']
        mig_ref = kwargs['mig_ref_id']
        count = 0
        network = self.nova.networks.find(label="private")
        flavor = self._flavor_create(kwargs['id'], kwargs['memory'],
                                     kwargs['vcpus'], int(kwargs['root_gb']))
        for disk in disks:
            image_name = "%s_%s" % (mig_ref, count)
            self._upload_image_to_glance(image_name, disk[str(count)])
            if count == 0:
                try:
                    image_id = self.nova.images.find(name=image_name)
                except Exception as ex:
                    LOG.error(_LE("Glance Image Not Found, id: %s"), image_id)
                    raise
                self.nova.servers.create(name=kwargs['name'],
                                         image=image_id.id,
                                         flavor=flavor.id,
                                         nics=[{'net-id': network.id}])
            else:
                img = self.glance.images.find(name=image_name)
                self.cinder.volumes.create(
                    display_name="%s_vol" % kwargs['name'],
                    size=8,
                    imageRef=img.id)
            count += 1
