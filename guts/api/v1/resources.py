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

"""The source resources."""

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

authorize = extensions.extension_authorizer('migration', 'resources')


class ResourcesController(wsgi.Controller):
    """The resource API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(ResourcesController, self).__init__()

    def _notify_source_error(self, ctxt, method, err,
                             source=None, id=None, name=None):
        payload = dict(sources=source, name=name, id=id, error_message=err)
        rpc.get_notifier('source').error(ctxt, method, payload)

    def _notify_source_info(self, ctxt, method, source):
        payload = dict(sources=source)
        rpc.get_notifier('source').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Resources."""
        context = req.environ['guts.context']
        db_resources = objects.ResourceList.get_all(context)

        resources = []
        for r in db_resources:
            resource = {}
            resource['id'] = r.id
            resource['name'] = r.name
            resource['type'] = r.type
            resource['migrated'] = r.migrated
            resource['hypervisor_name'] = r.source_hypervisor

            resources.append(resource)
        return dict(resources=resources)

    def show(self, req, id):
        """Returns data about given resource."""
        context = req.environ['guts.context']
        try:
            r = objects.Resource.get(context, id)
        except exception.ResourceNotFound:
            raise webob.exc.HTTPNotFound()

        resource = {}
        resource['id'] = r.id
        resource['name'] = r.name
        resource['type'] = r.type
        resource['migrated'] = r.migrated
        resource['source'] = r.source_hypervisor
        resource['properties'] = r.properties

        return {'resource': resource}


def create_resource(ext_mgr):
    return wsgi.Resource(ResourcesController(ext_mgr))
