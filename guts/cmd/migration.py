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
    server = service.Service.create(binary='guts-migration')
    service.serve(server)
    service.wait()
