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

=================
API Documentation
=================

Glossary
========

* **Source Hypervisor Types**

    These are types of source hypervisors, which are having migration driver implementation.
    E.g: OpenStack, VMWare, Hyper-V, etc...

* **Source Hypervisors**

    Instances of source hypervisor types, which contains VMs to migrate.
    E.g: AU_OpenStack is of type OpenStack; VMWare1 is of type VMWare, etc...

* **Source Instances**

    VMs/instances exist on source hypervisors.
    E.g: VM1, VM2 on AU_OpenStack, VM3, VM4 on VMWare1, etc...

* **Migrations**

    Instances of migration process. Which provides state and detailed information of migration processes.
    E.g: Mig1, which migrates VM3 from VMWare1 to AU_OpenStack.


API versions
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - GET
     - /
     - 200, 300
     - List API versions
   * - GET
     - /v1
     - 200, 203
     - Show API v1 details

API extensions
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - GET
     - /v1/{tenant_id}/extensions
     - 200, 300
     - List API extensions


Source Hypervisor Types API
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - POST
     - /v1/{tenant_id}/types
     - 202
     - Creates a source type
   * - GET
     - /v1/{tenant_id}/types
     - 200
     - List all source hypervisor types
   * - GET
     - /v1/{tenant_id}/types/detail
     - 200
     - List all source hypervisor types with details.
   * - GET
     - /v1/{tenant_id}/types/{type_id}
     - 200
     - Show details of a source hypervisor type
   * - PUT
     - /v1/{tenant_id}/types/{type_id}
     - 200
     - Updates source hypervisor type
   * - DELETE
     - /v1/{tenant_id}/types/{type_id}
     - 202
     - Delete source hypervisor type


Source Hypervisors API
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - POST
     - /v1/{tenant_id}/sources
     - 202
     - Creates a source
   * - GET
     - /v1/{tenant_id}/sources
     - 200
     - List all sources
   * - GET
     - /v1/{tenant_id}/sources/detail
     - 200
     - List all sources with details
   * - GET
     - /v1/{tenant_id}/sources/{source_id}
     - 200
     - Show details of a source hypervisor
   * - PUT
     - /v1/{tenant_id}/sources/{source_id}
     - 200
     - Updates source
   * - DELETE
     - /v1/{tenant_id}/sources/{source_id}
     - 202
     - Delete source


Source Instances API
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - GET
     - /v1/{tenant_id}/vms
     - 200
     - List all VMs
   * - GET
     - /v1/{tenant_id}/vms/detail
     - 200
     - List all VMs with details
   * - GET
     - /v1/{tenant_id}/vms/{vm_id}
     - 200
     - Show details of a VM

Migrations API
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 40 30 40

   * - Method
     - URL
     - Response Codes
     - Description
   * - POST
     - /v1/{tenant_id}/migrations
     - 202
     - Creates a migration process
   * - GET
     - /v1/{tenant_id}/migrations
     - 200
     - List all migrations
   * - GET
     - /v1/{tenant_id}/migrations/detail
     - 200
     - List all migrations with details
   * - GET
     - /v1/{tenant_id}/migrations/{migration_id}
     - 200
     - Show details of a migration
   * - DELETE
     - /v1/{tenant_id}/sources/{source_id}
     - 202
     - Delete source
