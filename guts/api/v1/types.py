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

"""The source hypervisor type & its driver path."""

import six
import webob

from oslo_log import log as logging
from oslo_utils import importutils

from guts.api import extensions
from guts.api.openstack import wsgi
from guts.api.views import types as views_types
from guts import exception
from guts.migration import types
from guts import rpc
from guts import utils

LOG = logging.getLogger(__name__)

authorize = extensions.extension_authorizer('migration', 'types_manage')


def validate_type_driver(source_type_driver):
    try:
        importutils.import_module(source_type_driver)
    except ImportError as err:
        raise exception.SourceTypeDriverNotFound(
            type_driver=source_type_driver,
            message=err.message)


class TypesController(wsgi.Controller):
    """The source hypervisor types API controller for the OpenStack API."""
    _view_builder_class = views_types.ViewBuilder

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(TypesController, self).__init__()

    def _notify_source_type_error(self, ctxt, method, err,
                                  source_type=None, id=None, name=None):
        payload = dict(
            source_types=source_type, name=name, id=id, error_message=err)
        rpc.get_notifier('sourceType').error(ctxt, method, payload)

    def _notify_source_type_info(self, ctxt, method, source_type):
        payload = dict(source_types=source_type)
        rpc.get_notifier('sourceType').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Source Hypervisor Types."""
        context = req.environ['guts.context']
        stypes = types.get_all_types(context)
        stypes = list(stypes.values())
        req.cache_resource(stypes, name='types')
        return self._view_builder.index(req, stypes)

    def show(self, req, id):
        """Returns data about given source hypervisor type."""
        context = req.environ['guts.context']
        try:
            stype = types.get_source_type(context, id)
            req.cache_resource(stype, name='type')
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        return self._view_builder.show(req, stype)

    def create(self, req, body):
        """Creates a new source hypervisor type."""
        ctxt = req.environ['guts.context']

        authorize(ctxt)

        stype = body['source_type']
        name = stype.get('name', None)
        driver = stype.get('driver')
        description = stype.get('description')

        if name is None or len(name.strip()) == 0:
            msg = "Source type name can not be empty."
            raise webob.exc.HTTPBadRequest(explanation=msg)

        if driver is None or len(driver.strip()) == 0:
            msg = "Source type driver can not be empty."
            raise webob.exc.HTTPBadRequest(explanation=msg)

        utils.check_string_length(name, 'Type name',
                                  min_length=1, max_length=255)

        utils.check_string_length(driver, 'Source Type driver',
                                  min_length=1, max_length=255)

        validate_type_driver(driver)

        if description is not None:
            utils.check_string_length(description, 'Type description',
                                      min_length=0, max_length=255)

        try:
            types.create(ctxt,
                         name,
                         driver,
                         description=description)

            stype = types.get_source_type_by_name(ctxt, name)
            req.cache_resource(stype, name='types')
            self._notify_source_type_info(
                ctxt, 'source_type.create', stype)

        except exception.SourceTypeExists as err:
            self._notify_source_type_error(
                ctxt, 'source_type.create', err, source_type=stype)
            raise webob.exc.HTTPConflict(explanation=six.text_type(err))
        except exception.SourceTypeNotFoundByName as err:
            self._notify_source_type_error(
                ctxt, 'source_type.create', err, name=name)
            raise webob.exc.HTTPNotFound(explanation=err.msg)

        return self._view_builder.show(req, stype)

    def delete(self, req, id):
        """Delete given source type."""
        context = req.environ['guts.context']
        authorize(context)

        # TODO(Bharat): Enable this later.
        # if self._source_type_in_use(context, type_id):
        #    expl = _('Cannot delete source type. Source type in use.')
        #    raise webob.exc.HTTPBadRequest(explanation=expl)
        # else:
        try:
            types.source_type_delete(context, id)
        except exception.SourceTypeNotFound as ex:
            raise webob.exc.HTTPNotFound(explanation=ex.msg)

        return webob.Response(status_int=202)


def create_resource(ext_mgr):
    return wsgi.Resource(TypesController(ext_mgr))
