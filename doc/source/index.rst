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


==============================
Welcome to GUTS Documentation!
==============================

Overview
~~~~~~~~

**GUTS**, a workload migration engine designed to automate the moving process
of existing workloads and virtual machines from various traditional hypervisor
infrastructure on to OpenStack cloud platform.

When moving from traditional virtualised environments to OpenStack, one of the
most thorny problems is migrating VMs from existing platforms such as VMWare or
Hyper-V to an OpenStack cloud. Most of the time, this process can involve time
consuming, repetitive and complicated steps like moving machines with multiple
virtual disks, removal or installation of customised hypervisor-specific tools,
and manually copying the data across.

GUTS solves these problems by providing an automated, efficient and robust
way to migrate VMs from existing virtualised environments to OpenStack.

GUTS is an open-source project consisting of several source code repositories:

* `guts`_ - is the main repository. It contains code for GUTS migration engine
  and GUTS API server.
* `guts-dashboard`_ - GUTS UI implemented as a plugin for OpenStack
  Dashboard.
* `python-gutsclient`_ - Client library and CLI client for GUTS.

This documentation offers information on how GUTS works and how to use it and
contribute to the project.

The document for GUTS dashboard is also available `here
<http://guts-dashboard.readthedocs.org>`_.

.. Links

.. _guts: https://github.com/aptira/guts/
.. _guts-dashboard: https://github.com/aptira/guts-dashboard/
.. _python-gutsclient: https://github.com/aptira/python-gutsclient/


Contents
~~~~~~~~

.. toctree::
   :maxdepth: 2

   installation-guide.rst
   configuration-reference.rst
   user-guide.rst
   developer-guide.rst
   getting-involved.rst
