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

"""Command-line flag library.

Emulates gflags by wrapping cfg.ConfigOpts.

The idea is to move fully to cfg eventually, and this wrapper is a
stepping stone.

"""

import socket

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import netutils


CONF = cfg.CONF
logging.register_options(CONF)

core_opts = [
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help='File name for the paste.deploy config for guts-api'),
    cfg.StrOpt('state_path',
               default='/var/lib/guts',
               deprecated_name='pybasedir',
               help="Top-level directory for maintaining guts's state"), ]

debug_opts = [
]

CONF.register_cli_opts(core_opts)
CONF.register_cli_opts(debug_opts)

global_opts = [
    cfg.StrOpt('my_ip',
               default=netutils.get_my_ipv4(),
               help='IP address of this host'),
    cfg.StrOpt('glance_host',
               default='$my_ip',
               help='Default glance host name or IP'),
    cfg.IntOpt('glance_port',
               default=9292,
               min=1, max=65535,
               help='Default glance port'),
    cfg.IntOpt('glance_api_version',
               default=1,
               help='Version of the glance API to use'),
    cfg.StrOpt('glance_api_server',
                default='http://$glance_host:$glance_port/v$glance_api_version',
                help='A list of the URLs of glance API servers available to '
                     'cinder ([http[s]://][hostname|ip]:port). If protocol '
                     'is not specified it defaults to http.'),
    cfg.StrOpt('project_domain_name',
               default='default',
               help="Project domain name required to connect to Nova."),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier. '
                    'It is not necessarily a host name, FQDN, or IP address.'),
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Enable monkey patching'),
    cfg.StrOpt('migration_topic',
               default='guts-migration',
               help='The topic that migration nodes listen on'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules/decorators to monkey patch'),
    cfg.StrOpt('rootwrap_config',
               default='/etc/guts/rootwrap.conf',
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
    cfg.StrOpt('auth_strategy',
               default='keystone',
               choices=['noauth', 'keystone'],
               help='The strategy to use for auth. Supports noauth or keystone.'),
    cfg.BoolOpt('api_rate_limit',
                default=True,
                help='Enables or disables rate limit of the API.'),
    cfg.MultiStrOpt('osapi_migration_extension',
                    default=['guts.api.contrib.standard_extensions'],
                    help='osapi migration extension to load'),
    cfg.StrOpt('migration_api_class',
               default='guts.migration.api.API',
               help='The full class name of the migration API class to use'),
    cfg.StrOpt('migration_manager',
               default='guts.migration.manager.MigrationManager',
               help='Full class name for the Manager for migration'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='Maximum time since last check-in for a service to be '
                    'considered up')
]

CONF.register_opts(global_opts)
