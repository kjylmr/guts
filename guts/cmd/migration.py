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

import sys
import eventlet

from oslo_config import cfg
from oslo_log import log as logging

from guts import config
from guts import i18n
from guts import objects
from guts import service

# TODO: Is this needed?
eventlet.monkey_patch()

i18n.enable_lazy()


CONF = cfg.CONF


def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "guts")
    objects.register_all()
    server = service.Service.create(binary='guts-migration',
                                    topic=CONF.migration_topic)
    service.serve(server)
    service.wait()
