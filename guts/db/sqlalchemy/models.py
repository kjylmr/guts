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

"""
SQLAlchemy models for guts data.
"""

from oslo_config import cfg
from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean


CONF = cfg.CONF
BASE = declarative_base()


class GutsBase(models.TimestampMixin,
               models.ModelBase):
    """Base class for Guts Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def delete(self, session):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)


class Hypervisors(BASE, GutsBase):
    """Represent hypervisors"""
    __tablename__ = "hypervisors"
    id = Column(String(36), primary_key=True)
    name = Column(String(64))
    driver = Column(String(64))
    type = Column(String(36))
    properties = Column(String(2048))
    credentials = Column(String(2048))
    capabilities = Column(String(36))
    exclude = Column(String(36))
    registered_host = Column(String(36))


class Resources(BASE, GutsBase):
    """Represent resources to migrate."""
    __tablename__ = "resources"
    id = Column(String(36), primary_key=True)
    name = Column(String(36))
    id_at_source = Column(String(36))
    type = Column(String(36))
    properties = Column(String(1024))
    migrated = Column(Boolean, default=False)
    source_hypervisor = Column(String(36), ForeignKey('hypervisors.id'))


class Migrations(BASE, GutsBase):
    """Represent migration."""
    __tablename__ = "migrations"
    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    description = Column(String(255))
    migration_status = Column(String(255))
    migration_event = Column(String(255))
    resource_id = Column(String(36),
                         ForeignKey('resources.id'))
    destination_hypervisor = Column(String(36),
                                    ForeignKey('hypervisors.id'))


class Service(BASE, GutsBase):
    """Represents a running service on a host."""
    __tablename__ = 'services'
    id = Column(String(36), primary_key=True)
    host = Column(String(255))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    disabled_reason = Column(String(255))
    modified_at = Column(DateTime)
    rpc_current_version = Column(String(36))
    rpc_available_version = Column(String(36))
    object_current_version = Column(String(36))
    object_available_version = Column(String(36))
