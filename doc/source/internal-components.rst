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

GUTS employs OpenStack Identity service for authentication; OpenStack
Compute service to boot instance; OpenStack Image service to store and
retrieve disk images; and OpenStack Dashboard to offer users an UI for GUTS.

GUTS consists of the following components:

**guts-api** service:

  * Accepts and responds to end user migration API calls.
  * Enforces some policies and initiates most orchestration activities,
    such as start migration process.
  * guts-api listens on ``7000`` port by default.

**guts-scheduler** service:

  * Schedules migration process.
  * Takes a migration request from the queue and determines on which
    migration server host it runs.
  * Selects a migration node based on conversion space available on the
    node.

**guts-migration** service:

  * A worker daemon that creates and manages migration of VM instances
    through hypervisor APIs. For example:

    - VSphere API for VMWare

    - Hyper-V API for Hyper-V

  * Migration process is fairly complex. Basically, the daemon accepts actions
    from queue and performs a series of system commands such as downloading
    disk images from source hypervisor, uploading to Glance, launching a new
    VM instance in Nova, and updating its state in database. And of course,
    ``guts-migration`` can get it all done automatically. 

**python-gutsclient**:

  * Empowers users to manage migration process with client libraries and a CLI.

**The queue**

  * A central hub for passing messages between daemons.
  * Usually implemented with `RabbitMQ <http://www.rabbitmq.com/>`__,
    but can be implemented with an AMQP message queue, such as `Apache
    Qpid <http://qpid.apache.org/>`__ or `ZeroMQ
    <http://www.zeromq.org/>`__.

**SQL database**

  * Stores most build-time and run-time states for migration, including:

    -  Source hypervisor types

    -  Source hypervisors and connection parameters

    -  Available VMs, Flavors and Networks

  * Theoretically, GUTS can support any database that SQL-Alchemy supports.
  * Common databases are SQLite3, MySQL, and PostgreSQL.
