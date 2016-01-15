

from guts.image import glance as image_api
from guts.compute import nova as nova_api
from guts import db


DEFAULT_NETWORK_ID = 'dbfaffc0-f4f5-4efe-9ced-3f16e6333bc5'

MIGRATION_EVENTS = ['INIT', 'FETCHING_IMAGES', 'CONVERTING_IMAGES',
                    'PUSHING_TO_GLANCE', 'BOOTING_IMAGES', 'FAILED',
                    'COMPLETED']

MIGRATION_STATUS = ['FAILED', 'IN-PROGRESS', 'COMPLETED']


class BaseMigration(object):

    def __init__(self, ctxt=None, migration_ref=None, vm=None):
        self.ctxt = None
        self.migration_ref = None
        self.vm = None

    def update_migration(self, **params):
        if 'migration_event' in params:
            if params['migration_event'] not in MIGRATION_EVENTS:
                raise Exception("Invalid migration event type")
        if 'migration_status' in params:
            if params['migration_status'] not in MIGRATION_STATUS:
                raise Exception("Invalid migration status type")
        db.migration_update(self.ctxt, self.migration_ref.id, params)

    def push_to_glance(self):
        self.update_migration(migration_event="PUSHING_TO_GLANCE")
        return image_api.create_image(self.ctxt,
                                      self.vm._prepare_image_meta(),
                                      self.vm.target_disk_path)

    def boot_image(self, image_id, flavor=3, net_id=DEFAULT_NETWORK_ID):
        self.update_migration(migration_event="BOOTING_IMAGES")
        server_info = {
            'name': self.vm.name,
            'image': image_id,
            'flavor': flavor,
            'nics': [{"net-id": net_id}]
        }
        nova_api.boot_server(self.ctxt, server_info)
