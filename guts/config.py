
from oslo_log import log
from oslo_config import cfg
from oslo_utils import importutils

from guts import version
from guts import rpc

importutils.import_module('guts.common.config')

CONF = cfg.CONF

# TODO: modify finally to suit GUTS requirements
_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                       'qpid=WARN', 'sqlalchemy=WARN', 'suds=INFO',
                       'oslo_service=INFO', 'oslo_concurrency=INFO',
                       'oslo_messaging=INFO', 'iso8601=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystonemiddleware=WARN', 'routes.middleware=WARN', ]

_DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                   '%(levelname)s %(name)s [%(request_id)s '
                                   '%(user_identity)s] %(instance)s'
                                   '%(message)s')


def parse_args(args=None, default_config_files=None):
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    log.register_options(CONF)
    # TODO: Use default sql connection (sqlite), in case not provided
    # as part of config file.

    rpc.set_defaults(control_exchange='guts')
    CONF(args[1:],
         project='guts',
         version=version.version_string(),
         default_config_files=default_config_files)
    rpc.init(CONF)
