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

============
Architecture
============

**GUTS** primarily consists of a set of Python daemons, though it
requires and integrates with a number of native system components for
databases, messaging and migration capabilities.

GUTS architecture diagram looks like::

                                                                                    +-----------------+
                                                                                    |                 |
                                                                                    |      VMWare     |
                                                                                 +->|Source Hypervisor|
 +-----------+                                                +---------------+  |  |                 |
 |           |                                                |               |  |  +-----------------+
 |Guts Client+--+                                          +->|guts-migration +--+
 |           |  |   +--------------+   +----------------+  |  |               |
 +-----------+  +-->|              |   |                +--+  +---------------+
                    |   guts-api   +-->| guts-scheduler |
 +-----------+  +-->|              |   |                +--+  +---------------+
 |           |  |   +--------------+   +----------------+  |  |               |
 |  Horizon  +--+                                          +->|guts-migration +--+
 |           |                                                |               |  |  +-----------------+
 +-----------+                                                +---------------+  |  |                 |
                                                                                 +->|    OpenStack    |
                                                                                    | Dest Hypervisor |
                                                                                    |                 |
                                                                                    +-----------------+


**guts-api**:

* Accepts and responds to end user migration API calls.
* Exposes RESTful APIs on the port 7000

**guts-migration**:

* A worker daemon that migrates VMs from source hypervisor to OpenStack
* Communicates with Glance, Nova and Neutron to create new VM on OpenStack
