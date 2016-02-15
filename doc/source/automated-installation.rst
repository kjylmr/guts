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

==================================
Automated Installation (Devstack)
==================================

GUTS also provides an automated way to install and configure its
components through devstack plugin.

Devstack-plugin:
  * Installs and configures guts-api and guts-migration
  * Sets up guts command line client python-gutsclient
  * Provides user interface, by configuring horizon plugin


Steps to deploy GUTS through devstack:

1. Select a Linux Distribution
  * Currently GUTS supports Ubuntu 14.04 (Trusty), Fedora 22 (or Fedora
    23) and CentOS/RHEL 7.

2. Install Selected OS
  * In order to correctly install all the dependencies, we assume a
    specific minimal version of the supported distributions to make it
    as easy as possible. We recommend using a minimal install of Ubuntu
    or Fedora server in a VM if this is your first time.

3. Download DevStack

.. code-block:: console

   $ git clone https://git.openstack.org/openstack-dev/devstack

4. Configure devstack/localrc to enable guts devstack-plugin

.. code-block:: console

    $ cd devstack/
    $ cat localrc
    [[local|localrc]]
    enable_plugin guts https://github.com/aptira/guts.git

5. Start the installation

.. code-block:: console

    $ cd devstack; ./stack.sh
