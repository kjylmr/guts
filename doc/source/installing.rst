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

===============
Installing Guts
===============

This section describes how to install Guts and Guts-Dashboard using Devstack.
1. Select a Linux Distribution
	* Currently GUTS supports Ubuntu 14.04 (Trusty), Fedora 22 (or Fedora 23) and CentOS/RHEL 7.
2. Install Selected OS
	* In order to correctly install all the dependencies, we assume a specific minimal version of the
          supported distributions to make it as easy as possible. We recommend using a minimal install of Ubuntu
          or Fedora server in a VM if this is your first time.
3. Follow Devstack documentation to setup a host for Devstack.
4. Create a localrc file as input to devstack.
5. The Guts service is not enabled by default, so it must be enabled in localrc before running stack.sh.
   This example localrc file shows all of the settings required for Murano and Murano-Dashboard.

.. code-block:: console
    > cat localrc
    [[local|localrc]]
    enable_plugin guts https://github.com/aptira/guts.git
..    

6. If user enable guts plugin in localrc file, guts plugin will automatically install guts-dashboard along with guts.
