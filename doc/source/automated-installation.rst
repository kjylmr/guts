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

=================================
Automated Installation (DevStack)
=================================

**GUTS** provides an automated way to install and configure its
components through a devstack plugin.

GUTS devstack plugin:
  * Installs and configures guts-api and guts-migration components
  * Sets up client library and CLI client python-gutsclient for GUTS
  * Installs `GUTS dashboard <http://guts-dashboard.readthedocs.org>`_ as
    plugin to Horizon.

Steps to deploy GUTS components using devstack:

1. Select a Linux distribution
  * Currently GUTS supports Ubuntu 14.04 (Trusty), Fedora 22 and 23, and
    CentOS/RHEL 7.

2. Install selected OS
  * In order to correctly install all the dependencies, we assume a
    specific minimal version of the supported distributions to make it
    as easy as possible. We recommend using a minimal install of Ubuntu or
    Fedora or CentOS server in a VM if this is your first time.

3. Download DevStack

.. code-block:: console

   $ git clone https://git.openstack.org/openstack-dev/devstack

4. Configure ``devstack/local.conf`` to enable GUTS devstack plugin

.. code-block:: console

    $ cd devstack/
    $ cat local.conf
    [[local|localrc]]
    enable_plugin guts https://github.com/aptira/guts.git

5. Start the installation

.. code-block:: console

    $ cd devstack; ./stack.sh
