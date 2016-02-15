..
    Copyright (c) 2015 Aptira Pty Ltd.
    All Rights Reserved.

       Licensed under the Apache License, Version 2.0 (the "License"); you may
       not use this file except in compliance with the License. You may obtain
       a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
       WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
       License for the specific language governing permissions and limitations
       under the License.

===================
Internal Components
===================

Use GUTS to migrate computing instances across cloud. The main modules
are implemented in Python.

GUTS interacts with OpenStack Identity for authentication; OpenStack
Compute service to boot instance; OpenStack Image service to store and
retrieving disk images; and OpenStack dashboard for the user and
administrative interface.

GUTS consists of the following areas and their components:

``guts-api`` service

  * Accepts and responds to end user migration API calls.
  * Enforces some policies and initiates most orchestration activities,
    such as start migration process.
  * guts-api listens on 7000 port by default.

``guts-migration`` service

  * A worker daemon that creates and manages migration of instances
    through hypervisor APIs. For example:

    - VSphere API for VMWare

    - Hyper-V API for Hyper-V

  * Processing is fairly complex. Basically, the daemon accepts actions
    from the queue and performs a series of system commands such as
    downloading disk images from source, uploading to glance, launching
    a KVM instance and updating its state in the database.

``guts`` client

  * Enables users to submit commands as a tenant administrator or end
    user.

``The queue``

  * A central hub for passing messages between daemons.
  * Usually implemented with `RabbitMQ <http://www.rabbitmq.com/>`__,
    but can be implemented with an AMQP message queue, such as `Apache
    Qpid <http://qpid.apache.org/>`__ or `ZeroMQ
    <http://www.zeromq.org/>`__.

``SQL database``

  * Stores most build-time and run-time states for a cloud
    infrastructure, including:

    -  Source hypervisor types

    -  Source hypervisors and connection params

    -  Available VMs, Flavors and Networks

  * Theoretically, GUTS can support any database that SQL-Alchemy
    supports.
  * Common databases are SQLite3 for test and development work, MySQL,
    and PostgreSQL.
