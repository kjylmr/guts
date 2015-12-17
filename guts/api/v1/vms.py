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

"""The source vms."""

import webob
from webob import exc

from oslo_log import log as logging

from guts.api import extensions
from guts.api.openstack import wsgi
from guts.api.views import vms as views_vms
from guts import exception
from guts.migration import vms
from guts import rpc

LOG = logging.getLogger(__name__)

authorize = extensions.extension_authorizer('migration', 'vms_manage')


class VMsController(wsgi.Controller):
    """The source VM API controller for the OpenStack API."""
    _view_builder_class = views_vms.ViewBuilder

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(VMsController, self).__init__()

    def _notify_vm_error(self, ctxt, method, err,
                         vm=None, id=None, name=None):
        payload = dict(vms=vm, name=name, id=id, error_message=err)
        rpc.get_notifier('vm').error(ctxt, method, payload)

    def _notify_vm_info(self, ctxt, method, vm):
        payload = dict(vms=vm)
        rpc.get_notifier('vm').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Source VMs."""
        context = req.environ['guts.context']
        svms = vms.get_all_vms(context)
        svms = list(svms.values())
        req.cache_resource(svms, name='vms')
        return self._view_builder.index(req, context, svms)

    def show(self, req, id):
        """Returns data about given source vm."""
        context = req.environ['guts.context']
        try:
            vm = vms.get_vm(context, id)
            req.cache_resource(vm, name='vm')
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.show(req, context, vm)

    def delete(self, req, id):
        """Delete given vm."""
        context = req.environ['guts.context']
        authorize(context)

        # TODO(Bharat): Enable this later.
        # if self._source_in_use(context, type_id):
        #    expl = _('Cannot delete source type. Source type in use.')
        #    raise webob.exc.HTTPBadRequest(explanation=expl)
        # else:
        try:
            vms.vm_delete(context, id)
        except exception.VMNotFound as ex:
            raise webob.exc.HTTPNotFound(explanation=ex.msg)

        return webob.Response(status_int=202)


def create_resource(ext_mgr):
    return wsgi.Resource(VMsController(ext_mgr))
