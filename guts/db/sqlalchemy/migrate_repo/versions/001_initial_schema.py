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
    source_hypervisor_types = Table(
        'source_hypervisor_types', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('name', String(length=255)),
        Column('deleted', Boolean),
        Column('description', String(255)),
        Column('extra_specs', String(255)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    source_hypervisors = Table(
        'source_hypervisors', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('name', String(length=255)),
        Column('deleted', Boolean),
        Column('description', String(255)),
        Column('source_hypervisor_type_id',
               Integer, ForeignKey('source_hypervisor_types.id'),
               nullable=False),
        Column('connection_params', String(255)),
        Column('extra_specs', String(255)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    source_hypervisor_instances = Table(
        'source_hypervisor_instances', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('name', String(length=255)),
        Column('deleted', Boolean),
        Column('description', String(255)),
        Column('no_of_disks', Integer),
        Column('migrated', Boolean),
        Column('source_hypervisor_id',
               Integer, ForeignKey('source_hypervisors.id'),
               nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    migrations = Table(
        'migrations', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('name', String(length=255)),
        Column('start_time', DateTime),
        Column('finish_time', DateTime),
        Column('migration_status', String(length=255)),
        Column('migration_event', String(length=255)),
        Column('dest_instance_id', String(length=255)),
        Column('description', String(255)),
        Column('deleted', Boolean),
        Column('source_instance_id',
               Integer, ForeignKey('source_hypervisor_instances.id'),
               nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    return [source_hypervisor_types,
            source_hypervisors,
            source_hypervisor_instances,
            migrations]


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    # create all tables
    # Take care on create order for those with FK dependencies
    tables = define_tables(meta)

    for table in tables:
        table.create()

    if migrate_engine.name == "mysql":
        tables = ["source_hypervisor_types",
                  "source_hypervisors",
                  "source_hypervisor_instances",
                  "migrations"]

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
