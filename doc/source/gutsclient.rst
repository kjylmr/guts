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

.. _client:

===========
Guts client
===========

Module python-gutsclient comes with CLI guts utility, that interacts with Guts migration

Installation
------------

To install latest guts CLI client run the following command in your shell:

.. code-block:: console

..

Alternatively you can checkout the latest version from
https://github.com/aptira/python-gutsclient.git

Using CLI client
----------------

In order to use the CLI, you must provide your OpenStack username, password,
tenant name or id, and auth endpoint. Use the corresponding arguments
(``--os-username``, ``--os-password``, ``--os-tenant-name`` or
``--os-tenant-id``, ``--os-auth-url`` and ``--murano-url``) or
set corresponding environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=password
    export OS_TENANT_NAME=tenant
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0
    export MURANO_URL=http://murano.example.com:7000/

Once you've configured your authentication parameters, you can run ``guts
help`` to see a complete listing of available commands and arguments and
``guts help <sub_command>`` to get help on specific subcommand.
