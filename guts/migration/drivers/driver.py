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


from guts.i18n import _
from guts import utils


class MigrationDriver(object):
    """This is the base class for all migration drivers."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self.host = kwargs.get('host')
        self.configuration = kwargs.get('configuration')
        self.hypervisor_ref = kwargs.get('hypervisor_ref')
        self._execute = execute
        self._stats = {}
        self._initialized = False


class SourceDriver(MigrationDriver):
    """This is the base class for all source hypervisor drivers."""
    def __init__(self, *args, **kwargs):
        super(SourceDriver, self).__init__(*args, **kwargs)
        if self.hypervisor_ref:
            self.exclude = self.hypervisor_ref.exclude.split(',')

    def get_instances_list(self):
        msg = _("The method get_instances_list is not implemented.")
        raise NotImplementedError(msg)

    def get_volumes_list(self):
        msg = _("The method get_volumes_list is not implemented.")
        raise NotImplementedError(msg)

    def get_networks_list(self):
        msg = _("The method get_networks_list is not implemented.")
        raise NotImplementedError(msg)


class DestinationDriver(MigrationDriver):
    """This is the base class for all destination hypervisor drivers."""
    def __init__(self, *args, **kwargs):
        super(DestinationDriver, self).__init__(*args, **kwargs)
