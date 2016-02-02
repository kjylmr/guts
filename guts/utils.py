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

"""Utilities and helper functions."""

import inspect
import os
import pyclbr
import re
import sys

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils
from oslo_utils import strutils
from oslo_utils import timeutils
from oslo_utils import units
import six

from guts import exception
from guts.i18n import _, _LI

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class QemuImgInfo(object):
    BACKING_FILE_RE = re.compile((r"^(.*?)\s*\(actual\s+path\s*:"
                                  r"\s+(.*?)\)\s*$"), re.I)
    TOP_LEVEL_RE = re.compile(r"^([\w\d\s\_\-]+):(.*)$")
    SIZE_RE = re.compile(r"(\d*\.?\d+)(\w+)?(\s*\(\s*(\d+)\s+bytes\s*\))?",
                         re.I)

    def __init__(self, cmd_output=None):
        details = self._parse(cmd_output or '')
        self.image = details.get('image')
        self.backing_file = details.get('backing_file')
        self.file_format = details.get('file_format')
        self.virtual_size = details.get('virtual_size')
        self.cluster_size = details.get('cluster_size')
        self.disk_size = details.get('disk_size')
        self.snapshots = details.get('snapshot_list', [])
        self.encrypted = details.get('encrypted')

    def __str__(self):
        lines = [
            'image: %s' % self.image,
            'file_format: %s' % self.file_format,
            'virtual_size: %s' % self.virtual_size,
            'disk_size: %s' % self.disk_size,
            'cluster_size: %s' % self.cluster_size,
            'backing_file: %s' % self.backing_file,
        ]
        if self.snapshots:
            lines.append("snapshots: %s" % self.snapshots)
        if self.encrypted:
            lines.append("encrypted: %s" % self.encrypted)
        return "\n".join(lines)

    def _canonicalize(self, field):
        # Standardize on underscores/lc/no dash and no spaces
        # since qemu seems to have mixed outputs here... and
        # this format allows for better integration with python
        # - i.e. for usage in kwargs and such...
        field = field.lower().strip()
        for c in (" ", "-"):
            field = field.replace(c, '_')
        return field

    def _extract_bytes(self, details):
        # Replace it with the byte amount
        real_size = self.SIZE_RE.search(details)
        if not real_size:
            raise ValueError(_('Invalid input value "%s".') % details)
        magnitude = real_size.group(1)
        unit_of_measure = real_size.group(2)
        bytes_info = real_size.group(3)
        if bytes_info:
            return int(real_size.group(4))
        elif not unit_of_measure:
            return int(magnitude)
        return strutils.string_to_bytes('%s%sB' % (magnitude, unit_of_measure),
                                        return_int=True)

    def _extract_details(self, root_cmd, root_details, lines_after):
        real_details = root_details
        if root_cmd == 'backing_file':
            # Replace it with the real backing file
            backing_match = self.BACKING_FILE_RE.match(root_details)
            if backing_match:
                real_details = backing_match.group(2).strip()
        elif root_cmd in ['virtual_size', 'cluster_size', 'disk_size']:
            # Replace it with the byte amount (if we can convert it)
            if root_details in ('None', 'unavailable'):
                real_details = 0
            else:
                real_details = self._extract_bytes(root_details)
        elif root_cmd == 'file_format':
            real_details = real_details.strip().lower()
        elif root_cmd == 'snapshot_list':
            # Next line should be a header, starting with 'ID'
            if not lines_after or not lines_after.pop(0).startswith("ID"):
                msg = _("Snapshot list encountered but no header found!")
                raise ValueError(msg)
            real_details = []
            # This is the sprintf pattern we will try to match
            # "%-10s%-20s%7s%20s%15s"
            # ID TAG VM SIZE DATE VM CLOCK (current header)
            while lines_after:
                line = lines_after[0]
                line_pieces = line.split()
                if len(line_pieces) != 6:
                    break
                # Check against this pattern in the final position
                # "%02d:%02d:%02d.%03d"
                date_pieces = line_pieces[5].split(":")
                if len(date_pieces) != 3:
                    break
                lines_after.pop(0)
                real_details.append({
                    'id': line_pieces[0],
                    'tag': line_pieces[1],
                    'vm_size': line_pieces[2],
                    'date': line_pieces[3],
                    'vm_clock': line_pieces[4] + " " + line_pieces[5],
                })
        return real_details

    def _parse(self, cmd_output):
        # Analysis done of qemu-img.c to figure out what is going on here
        # Find all points start with some chars and then a ':' then a newline
        # and then handle the results of those 'top level' items in a separate
        # function.
        #
        # TODO(harlowja): newer versions might have a json output format
        #                 we should switch to that whenever possible.
        #                 see: http://bit.ly/XLJXDX
        contents = {}
        lines = [x for x in cmd_output.splitlines() if x.strip()]
        while lines:
            line = lines.pop(0)
            top_level = self.TOP_LEVEL_RE.match(line)
            if top_level:
                root = self._canonicalize(top_level.group(1))
                if not root:
                    continue
                root_details = top_level.group(2).strip()
                details = self._extract_details(root, root_details, lines)
                contents[root] = details
        return contents


def get_root_helper():
    return 'sudo guts-rootwrap %s' % CONF.rootwrap_config


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = get_root_helper()
    return processutils.execute(*cmd, **kwargs)


def monkey_patch():
    """Patches decorators for all functions in a specified module.

    If the CONF.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.

    You can set decorators for each modules
    using CONF.monkey_patch_modules.
    The format is "Module path:Decorator function".
    Example: 'guts.api.ec2.cloud:' \
     guts.openstack.common.notifier.api.notify_decorator'

    Parameters of the decorator is as follows.
    (See guts.openstack.common.notifier.api.notify_decorator)

    :param name: name of the function
    :param function: object of the function
    """
    # If CONF.monkey_patch is not True, this function do nothing.
    if not CONF.monkey_patch:
        return
    # Get list of modules and decorators
    for module_and_decorator in CONF.monkey_patch_modules:
        module, decorator_name = module_and_decorator.split(':')
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                # On Python 3, unbound methods are regular functions
                predicate = inspect.isfunction if six.PY3 else inspect.ismethod
                for method, func in inspect.getmembers(clz, predicate):
                    setattr(
                        clz, method,
                        decorator("%s.%s.%s" % (module, key, method), func))
            # set the decorator for the function
            elif isinstance(module_data[key], pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                        decorator("%s.%s" % (module, key), func))


def find_config(config_path):
    """Find a configuration file using the given hint.

    :param config_path: Full or relative path to the config.
    :returns: Full path of the config, if it exists.
    :raises: `guts.exception.ConfigNotFound`

    """
    possible_locations = [
        config_path,
        os.path.join(CONF.state_path, "etc", "guts", config_path),
        os.path.join(CONF.state_path, "etc", config_path),
        os.path.join(CONF.state_path, config_path),
        "/etc/guts/%s" % config_path,
    ]

    for path in possible_locations:
        if os.path.exists(path):
            return os.path.abspath(path)

    raise exception.ConfigNotFound(path=os.path.abspath(config_path))


def walk_class_hierarchy(clazz, encountered=None):
    """Walk class hierarchy, yielding most derived classes first."""
    if not encountered:
        encountered = []
    for subclass in clazz.__subclasses__():
        if subclass not in encountered:
            encountered.append(subclass)
            # drill down to leaves first
            for subsubclass in walk_class_hierarchy(subclass, encountered):
                yield subsubclass
            yield subclass


def check_string_length(value, name, min_length=0, max_length=None):
    """Check the length of specified string.

    :param value: the value of the string
    :param name: the name of the string
    :param min_length: the min_length of the string
    :param max_length: the max_length of the string
    """
    if not isinstance(value, six.string_types):
        msg = ("%s is not a string or unicode") % name
        raise exception.InvalidInput(reason=msg)

    if len(value) < min_length:
        msg = ("%(name)s has a minimum character requirement of "
               "%(min_length)s.") % {'name': name, 'min_length': min_length}
        raise exception.InvalidInput(reason=msg)

    if max_length and len(value) > max_length:
        msg = ("%(name)s has more than %(max_length)s "
               "characters.") % {'name': name, 'max_length': max_length}
        raise exception.InvalidInput(reason=msg)


def convert_image(source, dest, out_format, run_as_root=True):
    """Convert image to other format."""

    cmd = ('qemu-img', 'convert',
           '-O', out_format, source, dest)

    start_time = timeutils.utcnow()
    execute(*cmd, run_as_root=run_as_root)
    duration = timeutils.delta_seconds(start_time, timeutils.utcnow())

    if duration < 1:
        duration = 1
    try:
        image_size = qemu_img_info(source, run_as_root=True).virtual_size
    except ValueError as e:
        msg = _LI("The image was successfully converted, but image size "
                  "is unavailable. src %(src)s, dest %(dest)s. %(error)s")
        LOG.info(msg, {"src": source,
                       "dest": dest,
                       "error": e})
        return

    fsz_mb = image_size / units.Mi
    mbps = (fsz_mb / duration)
    msg = ("Image conversion details: src %(src)s, size %(sz).2f MB, "
           "duration %(duration).2f sec, destination %(dest)s")
    LOG.debug(msg, {"src": source,
                    "sz": fsz_mb,
                    "duration": duration,
                    "dest": dest})

    msg = _LI("Converted %(sz).2f MB image at %(mbps).2f MB/s")
    LOG.info(msg, {"sz": fsz_mb, "mbps": mbps})


def qemu_img_info(path, run_as_root=True):
    """Return an object containing the parsed output from qemu-img info."""
    cmd = ('env', 'LC_ALL=C', 'qemu-img', 'info', path)
    if os.name == 'nt':
        cmd = cmd[2:]
    out, _err = execute(*cmd, run_as_root=run_as_root)
    return QemuImgInfo(out)
