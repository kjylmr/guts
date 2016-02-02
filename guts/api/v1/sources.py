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

import six
import webob

from oslo_log import log as logging

from guts.api import extensions
from guts.api.openstack import wsgi
from guts.api.views import sources as views_sources
from guts import exception
from guts.migration import sources
from guts.migration import vms
from guts import rpc
from guts import utils

LOG = logging.getLogger(__name__)

authorize = extensions.extension_authorizer('migration', 'sources_manage')


class SourcesController(wsgi.Controller):
    """The source hypervisor API controller for the OpenStack API."""
    _view_builder_class = views_sources.ViewBuilder

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
        hsources = sources.get_all_sources(context)
        hsources = list(hsources.values())
        req.cache_resource(hsources, name='sources')
        return self._view_builder.index(req, context, hsources)

    def show(self, req, id):
        """Returns data about given source hypervisor."""
        context = req.environ['guts.context']
        try:
            source = sources.get_source(context, id)
            req.cache_resource(source, name='source')
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        return self._view_builder.show(req, context, source)

    def create(self, req, body):
        """Creates a new source hypervisor."""
        ctxt = req.environ['guts.context']

        authorize(ctxt)

        source = body['source']
        name = source.get('name', None)
        stype = source.get('stype')
        connection_params = source.get('connection_params')
        description = source.get('description')

        if name is None or len(name.strip()) == 0:
            msg = "Source name can not be empty."
            raise webob.exc.HTTPBadRequest(explanation=msg)

        if connection_params is None or len(connection_params.strip()) == 0:
            msg = "Source connection params can not be empty."
            raise webob.exc.HTTPBadRequest(explanation=msg)

        utils.check_string_length(name, 'Hypervisor name',
                                  min_length=1, max_length=255)

        utils.check_string_length(connection_params,
                                  'Source connection parameters',
                                  min_length=1, max_length=255)

        if description is not None:
            utils.check_string_length(description, 'Source description',
                                      min_length=0, max_length=255)

        try:
            sources.create(ctxt,
                           name,
                           stype,
                           connection_params,
                           description=description)

            source = sources.get_source_by_name(ctxt, name)
            req.cache_resource(source, name='sources')
            self._notify_source_info(
                ctxt, 'source.create', source)

        except exception.SourceExists as err:
            self._notify_source_error(
                ctxt, 'source.create', err, source=source)
            raise webob.exc.HTTPConflict(explanation=six.text_type(err))
        except exception.SourceNotFoundByName as err:
            self._notify_source_error(
                ctxt, 'source_.create', err, name=name)
            raise webob.exc.HTTPNotFound(explanation=err.msg)

        vms.fetch_vms(ctxt, source.get('id'))
        return self._view_builder.show(req, ctxt, source)

    def delete(self, req, id):
        """Delete given source."""
        context = req.environ['guts.context']
        authorize(context)

        try:
            sources.source_delete(context, id)
        except exception.SourceNotFound as ex:
            raise webob.exc.HTTPNotFound(explanation=ex.msg)

        return webob.Response(status_int=202)


def create_resource(ext_mgr):
    return wsgi.Resource(SourcesController(ext_mgr))
