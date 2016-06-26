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

"""Hypervisors"""

import os
import re
import webob

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import importutils

from guts.api import common
from guts.api import extensions
from guts.api.openstack import wsgi
from guts.api.views import hypervisors as hypervisor_views
from guts import exception
from guts.i18n import _, _LI, _LW
from guts.migration import driver
from guts import objects
from guts.objects import base as objects_base
from guts import rpc
from guts import utils

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

authorize = extensions.extension_authorizer('hypervisor', 'hypervisors')


class HypervisorsController(wsgi.Controller):
    """The hypervisor API controller for the OpenStack API."""

    _view_builder_class = hypervisor_views.ViewBuilder
    HYPERVISOR_FILTER_OPTIONS = ('name', 'type', 'enabled')

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(HypervisorsController, self).__init__()

    def _notify_source_error(self, ctxt, method, err,
                             source=None, id=None, name=None):
        payload = dict(sources=source, name=name, id=id, error_message=err)
        rpc.get_notifier('source').error(ctxt, method, payload)

    def _notify_source_info(self, ctxt, method, source):
        payload = dict(sources=source)
        rpc.get_notifier('source').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Hypervisors"""
        return self._get_hypervisors(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of Hypervisors"""
        return self._get_hypervisors(req, is_detail=True)

    def _get_hypervisors(self, req, is_detail=False):
        context = req.environ['guts.context']
        filters = req.params.copy()

        if 'enabled' in filters.keys():
            filters['enabled'] = 1 if filters['enabled'].lower() == 'true' else 0

        marker, limit, offset = common.get_pagination_params(filters)
        sort_keys, sort_dirs = common.get_sort_params(filters)

        utils.remove_invalid_filter_options(context,
                                            filters,
                                            self.HYPERVISOR_FILTER_OPTIONS)

        hypervisors = objects.HypervisorList.get_all(context, filters, marker,
                                                     limit, offset, sort_keys,
                                                     sort_dirs)
        req.cache_resource(hypervisors.objects)
        if is_detail:
            hypervisors = self._view_builder.detail_list(req,
                                                         hypervisors.objects)
        else:
            hypervisors = self._view_builder.summary_list(req,
                                                          hypervisors.objects)
        return hypervisors

    def show(self, req, id):
        """Returns data about given hypervisor"""
        context = req.environ['guts.context']
        try:
            hypervisor = objects.Hypervisor.get_by_id(context, id)
        except Exception:
            raise webob.exc.HTTPNotFound()

        return self._view_builder.detail(req, hypervisor)

    def delete(self, req, id):
        """Deletes given hypervisor entry from the database"""
        context = req.environ['guts.context']
        LOG.info(_LI('Delete hypervisor with id: %s'), id, context=context)

        try:
            hypervisor = objects.Hypervisor.get_by_id(context, id)
            hypervisor.destroy()
        except exception.NotFound as error:
            raise webob.exc.HTTPNotFound(explanation=error.msg)
        except exception.GutsError as error:
            raise webob.exc.HTTPBadRequest(explanation=error.msg)

    @wsgi.action('os-enable_hypervisor')
    def enable(self, req, id, body):
        """Enables a specific hypervisor"""
        context = req.environ['guts.context']
        LOG.info(_LI('Enabling hypervisor: %s') % id, context=context)
        updates = {'enabled': True}
        hypervisor = objects.Hypervisor.get_by_id(context, id)
        hypervisor.update(updates)
        hypervisor.save()

    @wsgi.action('os-disable_hypervisor')
    def disable(self, req, id, body):
        """Disables a specific hypervisor"""
        context = req.environ['guts.context']
        LOG.info(_LI('Disabling hypervisor: %s') % id, context=context)
        updates = {'enabled': False}
        hypervisor = objects.Hypervisor.get_by_id(context, id)
        hypervisor.update(updates)
        hypervisor.save()

    def _get_creds_params(self, driver_path):
        try:
            drv = importutils.import_class(driver_path)
            return drv.get_creds_params()
        except Exception as error:
            raise webob.exc.HTTPNotFound(explanation=driver_path)

    def get_creds_params(self, req):
        """Get hypervisor credentials parameters"""
        context = req.environ['guts.context']
        params = req.params.copy()
        driver_path = params.get('driver_path')
        LOG.info(_LI('Getting connection parameters for the driver: %s') %
                 driver_path)
        return dict(creds=self._get_creds_params(driver_path))

    def _get_driver_capab(self, driver_path):
        try:
            drv = importutils.import_class(driver_path)
            return drv.get_driver_capab()
        except Exception as error:
            raise webob.exc.HTTPNotFound(explanation=driver_path)

    def get_driver_capab(self, req):
        """Get hypervisor credentials parameters"""
        context = req.environ['guts.context']
        params = req.params.copy()
        driver_path = params.get('driver_path')
        LOG.info(_LI('Getting driver capabilties: %s') %
                 driver_path)
        return dict(capabs=self._get_driver_capab(driver_path))

    def get_default_conversion_dir(self, req):
        """Get default conversion directory of the hypervisor"""
        return dict(con_dir=os.path.join(CONF.state_path, 'migrations'))

    def get_all_migration_hosts(self, req):
        """Get default conversion directory of the hypervisor"""
        context = req.environ['guts.context']
        return dict(nodes=utils._get_all_migration_hostnames(context))

    def create(self, req, body):
        """Create a new hypervisor"""
        context = req.environ['guts.context']
        LOG.debug('Create hypervisor request body: %s', body)
        hypervisor_properties = body['hypervisor']

        if not hypervisor_properties['name']:
            msg = _("Hypervisor name cannot be None.")
            raise webob.exc.HTTPBadRequest(explanation=msg)

        if not hypervisor_properties['driver']:
            msg = _("Hypervisor driver cannot be None.")
            raise webob.exc.HTTPBadRequest(explanation=msg)

        try:
            drv = importutils.import_class(hypervisor_properties['driver'])
        except ImportError as error:
            raise webob.exc.HTTPBadRequest(explanation=error.msg)

        # Checking the type of migration driver
        if issubclass(drv, driver.SourceDriver):
            hypervisor_properties['type'] = 'source'
        elif isinstance(drv, driver.DestinationDriver):
            hypervisor_properties['type'] = 'destination'
        else:
            msg = _("Unabled to find hypervisor type.")
            raise webob.exc.HTTPBadRequest(explanation=msg)

        # Allowed_hosts validation
        all_hosts = utils._get_all_migration_hostnames(context)
        allowed_nodes = []
        if not hypervisor_properties['allowed_hosts']:
            hypervisor_properties['allowed_hosts'] = all_hosts
        else:
            if '*' in hypervisor_properties['allowed_hosts']:
                LOG.info(_LI("Adding all migration nodes: %(nodes)s as "
                             "allowed_hosts to the hypervisor %(hypervisor)s."),
                         {'nodes': all_hosts,
                          'hypervisor': hypervisor_properties['name']})
                allowed_nodes = all_hosts
            else:
                for host in hypervisor_properties['allowed_hosts']:
                    if host not in all_hosts:
                        LOG.error(_LE("Ignoring allowed_host %(host)s. "
                                      "Reason: Host %(host)s is not running "
                                      "migration service."), {'host': host})
                    else:
                        allowed_nodes.append(host)
            if not allowed_nodes:
                msg = (_("Unable to load hypervisor: %(hypervisor)s. "
                         "Reason: No valid allowed_host found."),
                       {'hypervisor': hypervisor})
                LOG.error(msg)
                raise webob.exc.HTTPBadRequest(explantion=msg)
            hypervisor_properties['allowed_hosts'] = str(list(set(allowed_nodes)))

        # Checking regular expression for exclude resource using UUIDs.
        exclude_uuid_re = hypervisor_properties['exclude_resource_uuids']
        if exclude_uuid_re:
            try:
                re.compile(exclude_uuid_re)
            except re.error:
                LOG.exception(_LE("Invalid exclude_resource_uuids regex "
                                  "%(reg)s in %(hypervisor)s configuration."),
                              {'reg': exclude_uuid_re,
                               'hypervisor': hypervisor})
                raise webob.exc.HTTPBadRequest(explantion=error.msg)

        # Checking regular expression for exclude resource using Names.
        exclude_name_re = hypervisor_properties['exclude_resource_names']
        if exclude_name_re:
            try:
                re.compile(exclude_name_re)
            except re.error as error:
                LOG.exception(_LE("Invalid exclude_resource_names regex "
                                  "%(reg)s in %(hypervisor)s configuration."),
                              {'reg': exclude_name_re,
                               'hypervisor': hypervisor})
                raise webob.exc.HTTPBadRequest(explantion=error.msg)

        # Validating conversion directory.
        if not hypervisor_properties['conversion_dir']:
            con_dir = os.path.join(CONF.state_path, 'migrations')
            hypervisor_properties['converson_dir'] = con_dir

        # Validating hypervisor capabilities
        capabs = self._get_driver_capab(hypervisor_properties['driver'])
        if not hypervisor_properties['capabilities']:
            hypervisor_properties['capabilities'] = capabs

        given = hypervisor_properties['capabilities']
        for capab in given:
            if not capab:
                given.remove(capab)
                continue
            if capab not in capabs:
                msg = ("Capability %s doesn't supported by the driver %s." %
                       (capab, hypervisor_properties['driver']))
                raise webob.exc.HTTPBadRequest(explantion=msg)
        hypervisor_properties['capabilities'] = str(given)

        # TODO(Bharat): Add validation to hypervisor credentials
        creds = hypervisor_properties['credentials']
        if not creds:
            msg = "Hypervisor credentials cannot be None."
            raise webob.exc.HTTPBadRequest(explantion=msg)
        if 'password' in hypervisor_properties['credentials'].keys():
            pwd = hypervisor_properties['credentials']['password']
            encoded = utils.PasswordEncryption.encode(pwd)
            hypervisor_properties['credentials']['password'] = encoded
        hypervisor_properties['credentials'] = str(creds)

        try:
            name = hypervisor_properties['name']
            hypervisor_ref = objects.Hypervisor.get_by_name(context,
                                                            name)
            LOG.warn(_LW("Hypervisor %(hypervisor_name)s already exist. "
                         "So updating the exsting hypervisor."),
                     {'hypervisor_name': name})
            hypervisor_ref.update(hypervisor_properties)
            hypervisor_ref.save()
        except exception.HypervisorNotFound:
            LOG.debug("Creating new hypervisor entry for: %(hypervisor_name)s",
                      {'hypervisor_name': name})
            hypervisor_ref = objects.Hypervisor(context=context,
                                                **hypervisor_properties)
            hypervisor_ref.create()
        return self._view_builder.detail(req, hypervisor_ref)


def create_resource(ext_mgr):
    return wsgi.Resource(HypervisorsController(ext_mgr))
