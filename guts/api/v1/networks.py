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

"""The source networks."""

import webob

from oslo_config import cfg
from oslo_log import log as logging

from guts.api import extensions
from guts.api.openstack import wsgi
from guts import exception
from guts import objects
from guts import rpc

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

authorize = extensions.extension_authorizer('migration', 'networks')


class NetworksController(wsgi.Controller):
    """The network API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(NetworksController, self).__init__()

    def _notify_source_error(self, ctxt, method, err,
                             source=None, id=None, name=None):
        payload = dict(sources=source, name=name, id=id, error_message=err)
        rpc.get_notifier('source').error(ctxt, method, payload)

    def _notify_source_info(self, ctxt, method, source):
        payload = dict(sources=source)
        rpc.get_notifier('source').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Networks."""
        context = req.environ['guts.context']
        db_networks = objects.ResourceList.get_all_by_type(context, 'network')

        networks = []
        for i in db_networks:
            network = {}
            network['id'] = i.id
            network['name'] = i.name
            network['migrated'] = i.migrated
            network['hypervisor_name'] = i.source_hypervisor
            networks.append(network)

        return dict(networks=networks)

    def show(self, req, id):
        """Returns data about given network."""
        context = req.environ['guts.context']
        try:
            net = objects.Resource.get(context, id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        network = {}
        network['id'] = net.id
        network['name'] = net.name
        network['migrated'] = net.migrated
        network['source'] = net.source.source_hypervisor
        network['properties'] = net.properties

        return {'network': network}


def create_resource(ext_mgr):
    return wsgi.Resource(NetworksController(ext_mgr))
