

import glanceclient

from keystoneclient.auth.identity import v2
from keystoneclient import session
from oslo_config import cfg


CONF = cfg.CONF

GLANCE_API_VERSION = 1


def _get_admin_auth_url(context):
    try:
        return context.service_catalog[0]['endpoints'][0]['adminURL']
    except IndexError:
        raise "Invalid auth_url"


class GlanceAPI(object):

    def __init__(self, context):
        auth = v2.Token(auth_url=_get_admin_auth_url(context),
                        token=context.auth_token,
                        tenant_id=context.tenant)
        glance_session = session.Session(auth)
        self._gc = glanceclient.Client(GLANCE_API_VERSION,
                                       session=glance_session)

    def create(self, context, image_info):
        """Creates a new image record.

        :param context: The `guts.context.Context` object for the request
        :param image_info: A dict of information about the image that is
                           passed to the image registry.
        """
        # TODO: Optionally allow storing image bits to backend storage too.
        image_meta = _get_image_info(image_info)
        return self._gc.images.create(**image_meta)


def _get_image_info(image_info):
    return image_info


def create_image(ctxt, image_meta, image_path):
    glance_client = GlanceAPI(ctxt)
    image = glance_client.create(ctxt, image_meta)
    image.update(data=open(image_path, 'rb'))
    return image
