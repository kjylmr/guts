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

"""The destination hypervisors."""

import six
import webob

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from guts.api import extensions
from guts.api.openstack import wsgi
from guts import exception
from guts import objects
from guts import rpc
from guts import utils

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

authorize = extensions.extension_authorizer('migration', 'destinations')


class DestinationsController(wsgi.Controller):
    """The destination hypervisor API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(DestinationsController, self).__init__()

    def _notify_source_error(self, ctxt, method, err,
                             source=None, id=None, name=None):
        payload = dict(sources=source, name=name, id=id, error_message=err)
        rpc.get_notifier('source').error(ctxt, method, payload)

    def _notify_source_info(self, ctxt, method, source):
        payload = dict(sources=source)
        rpc.get_notifier('source').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Source Hypervisors."""
        context = req.environ['guts.context']
        src_services = objects.ServiceList.get_all_by_topic(context,
                                                            'guts-destination')
        now = timeutils.utcnow(with_timezone=True)

        destinations = []
        for service in src_services:
            dest = {}
            updated_at = service.updated_at
            delta = now - (service.updated_at or service.created_at)
            delta_sec = delta.total_seconds()
            alive = abs(delta_sec) <= CONF.service_down_time
            dest['status'] = (alive and "Up") or "Down"
            dest['host'] = service.host.split('@')[0]
            dest['hypervisor_name'] = service.host.split('@')[1]
            dest['id'] = service.id
            destinations.append(dest)
        return dict(destinations=destinations)

    def show(self, req, id):
        """Returns data about given destination hypervisor."""
        context = req.environ['guts.context']
        try:
            service = objects.Service.get(context, id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()
        now = timeutils.utcnow(with_timezone=True)
        dest = {}
        updated_at = service.updated_at
        delta = now - (service.updated_at or service.created_at)
        delta_sec = delta.total_seconds()
        alive = abs(delta_sec) <= CONF.service_down_time
        dest['status'] = (alive and "Up") or "Down"
        dest['host'] = service.host.split('@')[0]
        dest['hypervisor_name'] = service.host.split('@')[1]
        dest['id'] = service.id
        dest['binary'] = service.binary

        return {'destination': dest}

def create_resource(ext_mgr):
    return wsgi.Resource(DestinationsController(ext_mgr))
