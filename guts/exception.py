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

"""Guts base exception handling.

Includes decorator for re-raising Guts-type exceptions.

SHOULD include dedicated exception logging.

"""

import functools
import six
import sys
import webob.exc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from webob.util import status_generic_reasons
from webob.util import status_reasons

from guts.i18n import _, _LE
from guts import safe_utils


LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Make exception message format errors fatal.'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=500, title="", explanation=""):
        self.code = code
        # There is a strict rule about constructing status line for HTTP:
        # '...Status-Line, consisting of the protocol version followed by a
        # numeric status code and its associated textual phrase, with each
        # element separated by SP characters'
        # (http://www.faqs.org/rfcs/rfc2616.html)
        # 'code' and 'title' can not be empty because they correspond
        # to numeric status code and its associated text
        if title:
            self.title = title
        else:
            try:
                self.title = status_reasons[self.code]
            except KeyError:
                generic_code = self.code // 100
                self.title = status_generic_reasons[generic_code]
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class Error(Exception):
    pass


def _cleanse_dict(original):
    """Strip all admin_password, new_pass, rescue_pass keys from a dict."""
    return {k: v for k, v in six.iteritems(original) if "_pass" not in k}


def wrap_exception(notifier=None, get_notifier=None):
    """Wraps a method to catch any exceptions that may get thrown

    This decorator wraps a method to catch any exceptions that may
    get thrown. It also optionally sends the exception to the notification
    system.
    """

    def inner(f):
        def wrapped(self, context, *args, **kw):
            # Don't store self or context in the payload, it now seems to
            # contain confidential information.
            try:
                return f(self, context, *args, **kw)
            except Exception as e:
                with excutils.save_and_reraise_exception():
                    if notifier or get_notifier:
                        payload = dict(exception=e)
                        call_dict = safe_utils.getcallargs(f, context,
                                                           *args, **kw)
                        cleansed = _cleanse_dict(call_dict)
                        payload.update({'args': cleansed})

                        # If f has multiple decorators, they must use
                        # functools.wraps to ensure the name is
                        # propagated.
                        event_type = f.__name__

                        (notifier or get_notifier()).error(context,
                                                           event_type,
                                                           payload)

        return functools.wraps(f)(wrapped)
    return inner


class GutsException(Exception):
    """Base Guts Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        self.kwargs['message'] = message

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        for k, v in self.kwargs.items():
            if isinstance(v, Exception):
                self.kwargs[k] = six.text_type(v)

        if self._should_format():
            try:
                message = self.message % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_LE('Exception in string format operation'))
                for name, value in kwargs.items():
                    LOG.error(_LE("%(name)s: %(value)s"),
                              {'name': name, 'value': value})
                if CONF.fatal_exception_format_errors:
                    six.reraise(*exc_info)
                # at least get the core message out if something happened
                message = self.message
        elif isinstance(message, Exception):
            message = six.text_type(message)

        # NOTE(luisg): We put the actual message in 'msg' so that we can access
        # it, because if we try to access the message via 'message' it will be
        # overshadowed by the class' message attribute
        self.msg = message
        super(GutsException, self).__init__(message)

    def _should_format(self):
        return self.kwargs['message'] is None or '%(message)' in self.message

    def __unicode__(self):
        return six.text_type(self.msg)


class NotAuthorized(GutsException):
    message = _("Not authorized.")
    code = 403


class AdminRequired(NotAuthorized):
    message = _("You are not authorized to perform the \
requested action: admin_required")


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class NotFound(GutsException):
    message = _("Resource could not be found.")
    code = 404
    safe = True


class ConfigNotFound(GutsException):
    message = _("Could not find config at %(path)s")


class PasteAppNotFound(NotFound):
    message = _("Could not load paste app '%(name)s' from %(path)s")


class SourceTypeNotFound(NotFound):
    message = _("Source type %(source_type_id)s could not be found.")


class SourceTypeNotFoundByName(SourceTypeNotFound):
    message = _("Source type with name %(source_type_name)s "
                "could not be found.")


class VMNotFound(NotFound):
    message = _("Could not find VM with id '%(vm_id)s'")


class VMNotFoundByName(NotFound):
    message = _("Could not find VM with name '%(vm_name)s'")


class ServiceNotFound(NotFound):
    message = _("Service %(service_id)s could not be found.")


class Duplicate(GutsException):
    pass


class SourceTypeExists(Duplicate):
    message = _("Source Type %(id)s already exists.")


class Invalid(GutsException):
    message = _("Unacceptable parameters.")
    code = 400


class InvalidContentType(Invalid):
    message = _("Invalid content type %(content_type)s.")


class InvalidInput(Invalid):
    message = _("Invalid input received: %(reason)s")


class InvalidSource(Invalid):
    message = _("Invalid source: %(reason)s.")


class InvalidSourceType(Invalid):
    message = _("Invalid source type: %(reason)s.")


class SourceNotFound(NotFound):
    message = _("Source %(source_id)s could not be found.")


class SourceNotFoundByName(SourceNotFound):
    message = _("Source with name %(source_name)s "
                "could not be found.")


class SourceExists(Duplicate):
    message = _("Source %(id)s already exists.")


class MalformedRequestBody(GutsException):
    message = _("Malformed message body: %(reason)s")


class MigrationCreateFailed(GutsException):
    message = _("Failed to create migration %(name)s")


class MigrationNotFound(NotFound):
    message = _("Migration %(migration_id)s could not be found.")


class MigrationNotFoundByName(SourceNotFound):
    message = _("Migration with name %(migration_name)s "
                "could not be found.")


class MigrationExists(Duplicate):
    message = _("Migration %(id)s already exists.")


class SourceCreateFailed(GutsException):
    message = _("Failed to create source %(name)s")


class SourceTypeCreateFailed(GutsException):
    message = _("Failed to create source type %(name)s")


class SourceTypeDriverNotFound(NotFound):
    message = _("Source Type Driver %(type_driver)s could not be found.")


class HostBinaryNotFound(NotFound):
    message = _("Could not find binary %(binary)s on host %(host)s.")


class OrphanedObjectError(GutsException):
    message = _('Cannot call %(method)s on orphaned %(objtype)s object')


class ObjectActionError(GutsException):
    msg_fmt = _('Object action %(action)s failed because: %(reason)s')


class InstanceNotReadyForMigration(GutsException):
    message = _("Failed to create migration %(name)s. %(reason)s")
    safe = True


class MigrationValidationFailed(Invalid):
    pass


class InvalidPowerState(MigrationValidationFailed):
    message = _("Instance: %(instance_id)s cannot be migrated in its current "
                "power state. Please shutdown virtual instance and retry.")
