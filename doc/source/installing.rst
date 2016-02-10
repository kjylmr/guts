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

1. Follow Devstack documentation to setup a host for Devstack.
2. Create a localrc file as input to devstack.
3. The Guts service is not enabled by default, so it must be enabled in localrc before running stack.sh.
   This example localrc file shows all of the settings required for Murano and Murano-Dashboard.

.. code-block:: console

    > cat localrc
    [[local|localrc]]
    enable_plugin guts https://github.com/aptira/guts.git

4. If user enable guts plugin in localrc file, guts plugin will automatically install guts-dashboard along with guts.
