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

"""The FilterScheduler is for creating migration processes.

You can customize this scheduler by specifying your own migration Filters and
Weighing Functions.
"""

from oslo_config import cfg
from oslo_log import log as logging

from guts import exception
from guts.i18n import _
from guts.scheduler import driver
from guts.scheduler import scheduler_options

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class FilterScheduler(driver.Scheduler):
    """Scheduler that can be used for filtering and weighing."""
    def __init__(self, *args, **kwargs):
        super(FilterScheduler, self).__init__(*args, **kwargs)
        self.options = scheduler_options.SchedulerOptions()
        self.max_attempts = self._max_attempts()

    def schedule(self, context, topic, method, *args, **kwargs):
        """Schedule contract that returns best-suited host for this request."""
        pass

    def _max_attempts(self):
        max_attempts = CONF.scheduler_max_attempts
        if max_attempts < 1:
            raise exception.InvalidParameterValue(
                err=_("Invalid value for 'scheduler_max_attempts', "
                      "must be >=1"))
        return max_attempts
