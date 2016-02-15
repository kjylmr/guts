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


==================
GUTS Documentation
==================

Abstract
~~~~~~~~

**GUTS**, a workload migration engine designed to automatically move
existing workloads and virtual machines from various previous
generation virtualisation platforms on to OpenStack.

When organisations move from their existing virtualised infrastructures
to OpenStack, one of the biggest problems they face is the migration of
VMs running on VMWare, Hyper-V, etc., to OpenStack. Most of the time,
this process can involve time consuming, repetitive and complicated
steps like moving machines with multiple virtual disks, removal and
installation of customised hypervisor specific tools and manually
copying the data across.

GUTS solves this problem by providing an automated, efficient and robust
way to migrate VMs from existing clouds to OpenStack.

GUTS is an Open Source project that aims to make the move to an
OpenStack cloud easier. It addresses the various difficulties operators
and administrators face when migrating workloads from existing clouds on
to OpenStack.


Contents
~~~~~~~~

.. toctree::
   :maxdepth: 2

   installation-guide.rst
   configuration-reference.rst
   user-guide.rst
   developer-guide.rst
   getting-involved.rst
