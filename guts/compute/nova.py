
"""
Handles all requests to Nova.
"""

from novaclient import client as nova_client
from keystoneclient.auth.identity import v2
from keystoneclient import session


NOVA_API_VERSION = 2


def _get_admin_auth_url(ctxt):
    try:
        return ctxt.service_catalog[0]['endpoints'][0]['adminURL']
    except IndexError:
        raise Exception("Invalid auth_url")


class NovaAPI(object):

    def __init__(self, ctxt):
        auth = v2.Token(auth_url=_get_admin_auth_url(ctxt),
                        token=ctxt.auth_token,
                        tenant_id=ctxt.tenant)
        nova_session = session.Session(auth)
        self._client = nova_client.Client(NOVA_API_VERSION,
                                          session=nova_session)

    def boot(self, server_info):
        """Creates a new image record.

        :param context: The `guts.context.Context` object for the request
        :param image_info: A dict of information about the image that is
                           passed to the image registry.
        """
        # TODO: Optionally allow storing image bits to backend storage too.
        return self._client.servers.create(**server_info)


def boot_server(ctxt, server_info):
    nova_client = NovaAPI(ctxt)
    return nova_client.boot(server_info)
