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
        migrations = objects.MigrationList.get_all(context)

        migrations = []
        for m in migrations:
            migration = {}
            migration['id'] = m.id
            migration['name'] = m.name
            migration['resource_id'] = m.resource_id
            migration['migration_status'] = m.migration_status
            migration['migration_event'] = m.migration_event

            migrations.append(migration)
        return dict(migrations=migrations)

    def show(self, req, migration_id):
        """Returns data about given migration."""
        context = req.environ['guts.context']
        try:
            inst = objects.Resource.get(context, migration_id)
        except exception.NotFound:
            raise webob.exc.HTTPNotFound()

        migration = {}
        migration['id'] = m.id
        migration['name'] = m.name
        migration['resource_id'] = m.resource_id
        migration['migration_status'] = m.migration_status
        migration['migration_event'] = m.migration_event
        migration['description'] = m.description

        return {'migration': migration}

def create_resource(ext_mgr):
    return wsgi.Resource(MigrationsController(ext_mgr))
