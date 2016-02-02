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


from glanceclient import Client

from oslo_config import cfg

CONF = cfg.CONF


class GlanceAPI(object):
    def __init__(self, context):
        version = CONF.glance_api_version
        endpoint = CONF.glance_api_server
        self.glance_client = Client(version, endpoint=endpoint,
                                    token=context.auth_token)

    def create(self, image_info, image_path):
        """Creates a new image record."""
        try:
            img = self.glance_client.images.create(**image_info)
            img.update(data=open(image_path, 'rb'))
            return img
        except Exception:
            raise
