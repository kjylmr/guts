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

"""The source hypervisors."""

import webob

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import timeutils

from guts.api import extensions
from guts.api.openstack import wsgi
from guts import exception
from guts import objects
from guts.objects import base as objects_base
from guts import rpc

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

authorize = extensions.extension_authorizer('migration', 'sources')


class SourcesController(wsgi.Controller):
    """The source hypervisor API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(SourcesController, self).__init__()

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
        db_sources = objects.HypervisorList.get_all_by_type(context,
                                                         'source')
        sources = []
        for source in db_sources:
            s = {}
            s['status'] = "Up"
            s['host'] = source.registered_host
            s['hypervisor_name'] = source.name
            s['id'] = source.id
            sources.append(s)
        return dict(sources=sources)

    def show(self, req, id):
        """Returns data about given source hypervisor."""
        context = req.environ['guts.context']
        try:
            db_source = objects.Hypervisor.get(context, id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()
        source = {}
        source['status'] = "Up"
        source['host'] = db_source.registered_host
        source['hypervisor_name'] = db_source.name
        source['id'] = db_source.id
        source['binary'] = 'guts-source'

        return {'source': source}

    def create(self, req, body):
        """Create a new hypervisor"""
        context = req.environ['guts.context']
        LOG.debug('Create hypervisor request body: %s', body)
        hypervisor_values = body['source']
        if not hypervisor_values.get('conversion_dir'):
            hypervisor_values['conversion_dir'] = '/var/lib/guts/migrations'

        hyp_ref = objects.Hypervisor(context=context, **hypervisor_values)
        hyp_ref.create()
        source = {}
        source['status'] = "Up"
        source['host'] = hyp_ref.registered_host
        source['hypervisor_name'] = hyp_ref.name
        source['id'] = hyp_ref.id
        source['binary'] = 'guts-source'
        self._cast_to_manager(context, hyp_ref)
        return {'source': source}

    def _cast_to_manager(self, context, hypervisor_ref):
        host = hypervisor_ref.registered_host
        topic = ('guts-migration.%s' % (host))
        target = messaging.Target(topic=topic, version='1.8')
        serializer = objects_base.GutsObjectSerializer()
        client = rpc.get_client(target, version_cap=None,
                                serializer=serializer)

        ctxt = client.prepare(version='1.8')
        ctxt.cast(context, 'resource_update', hypervisor_ref=hypervisor_ref)


def create_resource(ext_mgr):
    return wsgi.Resource(SourcesController(ext_mgr))
