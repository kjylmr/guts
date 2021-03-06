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


"""Starter script for Guts Migration service."""

import eventlet
eventlet.monkey_patch()

import sys

from oslo_config import cfg
from oslo_log import log as logging

from guts import i18n
i18n.enable_lazy()

# Need to register global_opts
from guts.common import config  # noqa
from guts.i18n import _
from guts import objects
from guts import service
from guts import utils
from guts import version


CONF = cfg.CONF


def main():
    objects.register_all()
    CONF(sys.argv[1:], project='guts',
         version=version.version_string())
    logging.setup(CONF, "guts")
    utils.monkey_patch()
    launcher = service.get_launcher()
    LOG = logging.getLogger(__name__)
    source_service_started = False
    destination_service_started = False

    if CONF.enabled_source_hypervisors:
        for source in CONF.enabled_source_hypervisors:
            host = "%s@%s" % (CONF.host, source)
            try:
                server = service.Service.create(host=host,
                                                service_name=source,
                                                binary="guts-source")
            except Exception:
                msg = _('Source service %s failed to start.') % (host)
                LOG.exception(msg)
            else:
                launcher.launch_service(server)
                source_service_started = True

    if CONF.enabled_destination_hypervisors:
        for dest in CONF.enabled_destination_hypervisors:
            host = "%s@%s" % (CONF.host, dest)
            try:
                server = service.Service.create(host=host,
                                                service_name=dest,
                                                binary="guts-destination")
            except Exception:
                msg = _('Destination service %s failed to start.') % (host)
                LOG.exception(msg)
            else:
                launcher.launch_service(server)
                destination_service_started = True

    if not (source_service_started or destination_service_started):
        msg = _('No migration service(s) started successfully, terminating.')
        LOG.error(msg)
        sys.exit(1)

    launcher.wait()
