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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import Integer, MetaData, String, Table


def define_tables(meta):
    hypervisors = Table(
        'hypervisors', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('type', String(length=36)),
        Column('name', String(length=64)),
        Column('driver', String(length=512)),
        Column('credentials', String(length=2048)),
        Column('capabilities', String(length=36)),
        Column('properties', String(length=2048)),
        Column('exclude', String(length=36)),
        Column('deleted', Boolean),
        Column('registered_host', String(length=36)),
        Column('conversion_dir', String(length=36)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    resources = Table(
        'resources', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('type', String(length=36)),
        Column('id_at_source', String(length=36)),
        Column('name', String(length=36)),
        Column('properties', String(length=1024)),
        Column('deleted', Boolean),
        Column('migrated', Boolean),
        Column('source_hypervisor', String(length=255),
               ForeignKey('hypervisors.id'), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    migrations = Table(
        'migrations', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('name', String(length=255)),
        Column('description', String(255)),
        Column('resource_id',
               String(length=36), ForeignKey('resources.id'),
               nullable=False),
        Column('migration_status', String(length=255)),
        Column('migration_event', String(length=255)),
        Column('destination_hypervisor', String(length=36),
               ForeignKey('hypervisors.id'), nullable=False),
        Column('start_time', DateTime),
        Column('finish_time', DateTime),
        Column('deleted', Boolean),
        Column('extra_params', String(length=512)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    services = Table(
        'services', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('modified_at', DateTime),
        Column('deleted', Boolean),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('host', String(length=255)),
        Column('binary', String(length=255)),
        Column('topic', String(length=255)),
        Column('report_count', Integer, nullable=False),
        Column('disabled', Boolean),
        Column('disabled_reason', String(255)),
        Column('rpc_current_version', String(36)),
        Column('rpc_available_version', String(36)),
        Column('object_current_version', String(36)),
        Column('object_available_version', String(36)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    return [hypervisors, resources, migrations, services]


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    # create all tables
    # Take care on create order for those with FK dependencies
    tables = define_tables(meta)

    for table in tables:
        table.create()

    if migrate_engine.name == "mysql":
        tables = ['hypervisors', 'resources', 'migrations', 'services']

        migrate_engine.execute("SET foreign_key_checks = 0")
        for table in tables:
            migrate_engine.execute(
                "ALTER TABLE %s CONVERT TO CHARACTER SET utf8" % table)
        migrate_engine.execute("SET foreign_key_checks = 1")
        migrate_engine.execute(
            "ALTER DATABASE %s DEFAULT CHARACTER SET utf8" %
            migrate_engine.url.database)
        migrate_engine.execute("ALTER TABLE %s Engine=InnoDB" % table)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    tables = define_tables(meta)
    tables.reverse()
    for table in tables:
        table.drop()
