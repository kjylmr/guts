#!/usr/bin/env python
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

"""Starter script for All guts services.

This script attempts to start all the guts services in one process.  Each
service is started in its own greenthread.  Please note that exceptions and
sys.exit() on the starting of a service are logged and the script will
continue attempting to launch the rest of the services.

"""

import eventlet
eventlet.monkey_patch()

import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from guts import i18n
i18n.enable_lazy()

# Need to register global_opts
from guts.common import config   # noqa
from guts.i18n import _LE
from guts import objects
from guts import rpc
from guts import service
from guts import utils
from guts import version


CONF = cfg.CONF


def main():
    objects.register_all()
    CONF(sys.argv[1:], project='guts',
         version=version.version_string())
    logging.setup(CONF, "guts")
    LOG = logging.getLogger('guts.all')

    utils.monkey_patch()

    gmr.TextGuruMeditation.setup_autorun(version)

    rpc.init(CONF)

    launcher = service.process_launcher()
    # guts-api
    try:
        server = service.WSGIService('osapi_migration')
        launcher.launch_service(server, workers=server.workers or 1)
    except (Exception, SystemExit):
        LOG.exception(_LE('Failed to load osapi_migration'))

    # guts-migration
    try:
        launcher.launch_service(
            service.Service.create(binary='guts-migration'))
    except (Exception, SystemExit):
        LOG.exception(_LE('Failed to load guts-migration'))

    launcher.wait()
