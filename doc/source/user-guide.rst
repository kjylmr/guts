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

==========
User Guide
==========

GUTS is an open-source project that aims to make the move to an OpenStack cloud
easier. It addresses various difficulties that operators and administrators 
may face when migrating workloads from existing traditional virtualisation
platforms on to OpenStack cloud.

This guide shows GUTS users how to create and manage various migration entities
with the GUTS command line clients (CLI).

Manage Source Hypervisor Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * Create a new Source Hypervisor Type
    
    .. code-block:: console
    
       $ guts source-type-create --name VMWare --description "VMWare(VSphere) Source Hypervisor" guts.migration.drivers.vsphere
         +--------------------------------------+--------+
         |                  ID                  |  Name  |
         +--------------------------------------+--------+
         | 9bf19345-cb7b-47d3-89bc-b0ce2cd76216 | VMWare |
         +--------------------------------------+--------+
    
  * List all Source Hypervisor Types
    
    .. code-block:: console
    
       $ guts source-type-list
         +--------------------------------------+--------+--------------------------------+
         |                  ID                  |  Name  |             Driver             |
         +--------------------------------------+--------+--------------------------------+
         | 9bf19345-cb7b-47d3-89bc-b0ce2cd76216 | VMWare | guts.migration.drivers.vsphere |
         +--------------------------------------+--------+--------------------------------+
    
  * Show Source Hypervisor Type Details
    
    .. code-block:: console
    
       $ guts source-type-show VMWare
         +-------------+--------------------------------------+
         |   Property  |                Value                 |
         +-------------+--------------------------------------+
         | description |  VMWare(VSphere) Source Hypervisor   |
         |    driver   |    guts.migration.drivers.vsphere    |
         |      id     | 9bf19345-cb7b-47d3-89bc-b0ce2cd76216 |
         |     name    |                VMWare                |
         +-------------+--------------------------------------+
    
  * Update Source Hypervisor Type
    
    .. code-block:: console
    
       $ guts source-type-update VMWare --description "New Description"
         +-------------+--------------------------------------+
         |   Property  |                Value                 |
         +-------------+--------------------------------------+
         | description |           New Description            |
         |    driver   |    guts.migration.drivers.vsphere    |
         |      id     | 9bf19345-cb7b-47d3-89bc-b0ce2cd76216 |
         |     name    |                VMWare                |
         +-------------+--------------------------------------+
    
  * Delete Source Hypervisor Type
    
    .. code-block:: console
    
       $ guts source-type-delete VMWare
    
    
Manage Source Hypervisors
~~~~~~~~~~~~~~~~~~~~~~~~~
    
  * Create a new Source Hypervisor
    
    .. code-block:: console
    
       $ guts source-create --name MyVMWare1 --type VMWare --description "My VMWare(VSphere) Hypervisor" "host=<IP>;user=<USER>;password=<PASSWORD>;port=<PORT>"
         +--------------------------------------+-----------+------------------+-------------------------------+
         |                  ID                  |    Name   | Source Type Name |          Description          |
         +--------------------------------------+-----------+------------------+-------------------------------+
         | 7d5e45d5-1032-4ec9-924e-beb827a10c4e | MyVMWare1 |      VMWare      | My VMWare(VSphere) Hypervisor |
         +--------------------------------------+-----------+------------------+-------------------------------+
    
  * List all Source Hypervisors
    
    .. code-block:: console
    
       $ guts source-list
         +--------------------------------------+-----------+------------------+-------------------------------+
         |                  ID                  |    Name   | Source Type Name |          Description          |
         +--------------------------------------+-----------+------------------+-------------------------------+
         | 7d5e45d5-1032-4ec9-924e-beb827a10c4e | MyVMWare1 |      VMWare      | My VMWare(VSphere) Hypervisor |
         +--------------------------------------+-----------+------------------+-------------------------------+
    
  * Show Source Hypervisor Details
    
    .. code-block:: console
    
       $ guts source-show MyVMWare1
         +------------------------+----------------------------------------------------------------------------------+
         |        Property        |                                      Value                                       |
         +------------------------+----------------------------------------------------------------------------------+
         |   Connection String    |              host=<IP>;user=<USER>;password=<PASSWORD>;port=<PORT>               |
         |      Description       |                          My VMWare(VSphere) Hypervisor                           |
         |           ID           |                       7d5e45d5-1032-4ec9-924e-beb827a10c4e                       |
         |          Name          |                                    MyVMWare1                                     |
         | Source Hypervisor Type |                                      VMWare                                      |
         +------------------------+----------------------------------------------------------------------------------+
    
  * Update Source Hypervisor
    
    .. code-block:: console
    
       $ guts source-update MyVMWare1 --description "Some New Description"
         +------------------------+----------------------------------------------------------------------------------+
         |        Property        |                                      Value                                       |
         +------------------------+----------------------------------------------------------------------------------+
         |   Connection String    |              host=<IP>;user=<USER>;password=<PASSWORD>;port=<PORT>               |
         |      Description       |                               Some New Description                               |
         |           ID           |                       7d5e45d5-1032-4ec9-924e-beb827a10c4e                       |
         |          Name          |                                    MyVMWare1                                     |
         | Source Hypervisor Type |                                      VMWare                                      |
         +------------------------+----------------------------------------------------------------------------------+
    
  * Delete Source Hypervisor
    
    .. code-block:: console
    
       $ guts source-delete MyVMWare1
    
    
Manage Source Instances (VMs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
  * Fetch VM list from Source Hypervisor
    
    .. code-block:: console
    
       $ guts vm-fetch MyVMWare1
    
  * List all avalilable VMs
    
    .. code-block:: console
    
       $ guts vm-list
         +--------------------------------------+--------------------+-----------------+----------+-------------------+
         |                  ID                  |        Name        | Hypervisor Name | Migrated | Destination VM id |
         +--------------------------------------+--------------------+-----------------+----------+-------------------+
         | 12821516-7ff0-4a76-9b7b-bb56df54b300 |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         | 42326e52-471c-4f2a-b750-7b9ef33d41b9 |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         | 4dead0bc-bb3d-463d-90f0-76302c9368f4 |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         | b7d78ecd-71eb-4348-9129-df80ba9831b7 |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         | c0985ed3-d9c1-46e5-8b15-d9b5506ba66e |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         | faf28414-8184-4bac-9884-743821c398bf |      XXXXXXX       |    MyVMWare1    |  False   |         -         |
         +--------------------------------------+--------------------+-----------------+----------+-------------------+
    
  * Show Source VM Details
    
    .. code-block:: console
    
       $ guts vm-show 12821516-7ff0-4a76-9b7b-bb56df54b300
         +-------------------+--------------------------------------+
         |      Property     |                Value                 |
         +-------------------+--------------------------------------+
         | Destination VM ID |                 None                 |
         |  Hypervisor Name  |              MyVMWare1               |
         |         ID        | 12821516-7ff0-4a76-9b7b-bb56df54b300 |
         |    Is Migrated    |                False                 |
         |        Name       |            XXXXXXXXXXXXX             |
         |   UUID at Source  | 502ce17f-ab83-b13f-142e-cdc8c4a0a65e |
         +-------------------+--------------------------------------+
    
  * Delete Source VM
    
    .. code-block:: console
    
       $ guts vm-delete 12821516-7ff0-4a76-9b7b-bb56df54b300
    
    
Manage Migrations
~~~~~~~~~~~~~~~~~
    
  * Create a new Migration process
    
    .. code-block:: console
    
       $ guts create --name VM1_Migration --description "Sample VM1 Migration" MinimalUbuntu
         +--------------------------------------+---------------+--------+-------+----------------------+--------------------------------------+
         |                  ID                  |      Name     | Status | Event |     Description      |          Source Instance ID          |
         +--------------------------------------+---------------+--------+-------+----------------------+--------------------------------------+
         | efbb708d-b9c3-4f8d-85c7-d814994ccff4 | XXXXXXXXXXXXX |   -    |   -   | Sample VM1 Migration | 12821516-7ff0-4a76-9b7b-bb56df54b300 |
         +--------------------------------------+---------------+--------+-------+----------------------+--------------------------------------+
    
  * List all Migrations
    
    .. code-block:: console
    
       $ guts list
         +--------------------------------------+---------------+-----------+-------+----------------------+--------------------------------------+
         |                  ID                  |      Name     |  Status   | Event |     Description      |          Source Instance ID          |
         +--------------------------------------+---------------+-----------+-------+----------------------+--------------------------------------+
         | efbb708d-b9c3-4f8d-85c7-d814994ccff4 | XXXXXXXXXXXXX | COMPLETED |   -   | Sample VM1 Migration | 12821516-7ff0-4a76-9b7b-bb56df54b300 |
         +--------------------------------------+---------------+-----------+-------+----------------------+--------------------------------------+
    
  * Delete a Migration
    
    .. code-block:: console
    
       $ guts delete efbb708d-b9c3-4f8d-85c7-d814994ccff4
