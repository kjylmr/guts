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

import time

from keystoneclient.auth.identity import v3
from keystoneclient import session
from novaclient import client as novaclient

from oslo_config import cfg
from oslo_utils import units


NOVA_API_VERSION = 2

CONF = cfg.CONF


def _get_admin_auth_url(ctxt):
    for s in ctxt.service_catalog:
        if s['type'] == 'identity':
            return s['endpoints'][0]['adminURL']
    raise Exception("Identity admin URL not found.")


class NovaAPI(object):
    def __init__(self, ctxt):
        auth = v3.Token(auth_url=_get_admin_auth_url(ctxt),
                        token=ctxt.auth_token,
                        project_name=ctxt.project_name,
                        project_domain_name=CONF.project_domain_name)

        sess = session.Session(auth=auth)
        self._nc = novaclient.Client(NOVA_API_VERSION, session=sess)

    def create(self, ctxt, disks, vm_name):
        image_id = None
        volumes = []
        for disk in disks:
            if disk['index'] == '0':
                image_id = disk['image_id']
            else:
                volume = {'image_id': disk['image_id'],
                          'size': disk['size']}
                volumes.append(volume)

        if image_id is None:
            raise Exception("Glance Image Not Found.")

        name = vm_name
        image = self._nc.images.find(id=image_id)
        flavor = self._nc.flavors.find(name="m1.small")
        network = self._nc.networks.find(label="private")

        server = self._nc.servers.create(name=name, image=image.id,
                                         flavor=flavor.id,
                                         nics=[{'net-id': network.id}])
        self.create_volumes(volumes, server)
        return server.id

    def _create_volume_and_attach(self, volume, server):
        size = int((volume['size'] / units.Gi) + 1)
        vol = self._nc.volumes.create(size, imageRef=volume['image_id'],
                                      display_name=volume['image_id'])
        timeout = 180

        srv = self._nc.servers.find(id=server.id)
        v = self._nc.volumes.find(id=vol.id)
        while v.status != 'available' or srv.status != 'ACTIVE':
            if timeout < 0 or v.status == 'error' or srv.status == 'error':
                raise Exception("Unable to attach volume to server.")
            time.sleep(5)
            srv = self._nc.servers.find(id=server.id)
            v = self._nc.volumes.find(id=vol.id)
            timeout -= 5

        self._nc.volumes.create_server_volume(server.id, vol.id)

    def create_volumes(self, volumes, server):
        for volume in volumes:
            self._create_volume_and_attach(volume, server)
