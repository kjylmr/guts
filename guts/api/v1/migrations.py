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

"""Migrations."""

import ast
import webob

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from guts.api import extensions
from guts.api.openstack import wsgi
from guts import exception
from guts import objects
from guts.objects import base as objects_base
from guts import rpc

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

authorize = extensions.extension_authorizer('migration', 'migrations')


class MigrationsController(wsgi.Controller):
    """The migration API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        super(MigrationsController, self).__init__()

    def _notify_source_error(self, ctxt, method, err,
                             source=None, id=None, name=None):
        payload = dict(sources=source, name=name, id=id, error_message=err)
        rpc.get_notifier('source').error(ctxt, method, payload)

    def _notify_source_info(self, ctxt, method, source):
        payload = dict(sources=source)
        rpc.get_notifier('source').info(ctxt, method, payload)

    def index(self, req):
        """Returns the list of Migrations."""
        context = req.environ['guts.context']
        db_migrations = objects.MigrationList.get_all(context)

        migrations = []
        for m in db_migrations:
            migration = {}
            migration['id'] = m.id
            migration['name'] = m.name
            migration['resource_id'] = m.resource_id
            r = objects.Resource.get(context, m.resource_id)
            migration['resource_type'] = r.type
            migration['status'] = m.migration_status
            migration['event'] = m.migration_event
            migration['destination_hypervisor'] = m.destination_hypervisor

            migrations.append(migration)
        return dict(migrations=migrations)

    def show(self, req, id):
        """Returns data about given migration."""
        context = req.environ['guts.context']
        try:
            m = objects.Migration.get(context, id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        migration = {}
        migration['id'] = m.id
        migration['name'] = m.name
        migration['resource_id'] = m.resource_id
        r = objects.Resource.get(context, m.resource_id)
        migration['resource_type'] = r.type
        migration['status'] = m.migration_status
        migration['event'] = m.migration_event
        migration['destination_hypervisor'] = m.destination_hypervisor
        migration['description'] = m.description

        return {'migration': migration}

    def create(self, req, body):
        """Create a new migration process."""
        context = req.environ['guts.context']
        LOG.debug('Create migration request body: %s', body)
        mig_values = body['migration']
        dest_hypervisor = mig_values['destination_hypervisor']
        kwargs = {'name': mig_values['name'],
                  'description': mig_values['description'],
                  'resource_id': mig_values['resource_id'],
                  'migration_status': 'Initiating',
                  'migration_event': 'Scheduling',
                  'destination_hypervisor': dest_hypervisor,
                  'extra_params': mig_values['extra_params']}

        mig_ref = objects.Migration(context=context, **kwargs)
        mig_ref.create()

        migration = {}
        migration['id'] = mig_ref.id
        migration['name'] = mig_ref.name
        migration['resource_id'] = mig_ref.resource_id
        migration['status'] = mig_ref.migration_status
        migration['event'] = mig_ref.migration_event
        migration['destination_hypervisor'] = mig_ref.destination_hypervisor
        migration['description'] = mig_ref.description

        resource_ref = objects.Resource.get(context, mig_ref.resource_id)
        self._cast_to_source(context, mig_ref, resource_ref)
        return {'migration': migration}

    def _cast_to_source(self, context, mig_ref, resource_ref):
        src_host = resource_ref.source_hypervisor
        src_host = objects.Hypervisor.get(context, src_host)
        src_host = src_host.registered_host
        dest_ref = objects.Hypervisor.get(context, mig_ref.destination_hypervisor)
        dest_host = dest_ref.registered_host
        src_topic = ('guts-migration.%s' % (src_host))
        target = messaging.Target(topic=src_topic, version='1.8')
        serializer = objects_base.GutsObjectSerializer()
        client = rpc.get_client(target, version_cap=None,
                                serializer=serializer)

        ctxt = client.prepare(version='1.8')
        ctxt.cast(context, 'get_resource',
                  migration_ref=mig_ref,
                  resource_ref=resource_ref,
                  dest_host=dest_host)

    def delete(self, req, id):
        """Deletes given migration entry from database."""
        context = req.environ['guts.context']
        LOG.info(_LI("Delete migration with id: %s"), id, context=context)
        try:
            m = objects.Migration.get(context, id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()
        m.destroy()


def create_resource(ext_mgr):
    return wsgi.Resource(MigrationsController(ext_mgr))
