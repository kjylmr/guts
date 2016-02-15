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

===============================
Installing and Running Manually
===============================

Install And Configure Database
------------------------------

This section describes how to install and configure the Migration service, code-named guts, on the controller node.

Before you install and configure the Migration service, you must create a database, service credentials, and API endpoints.

To create the database, complete these steps:

#.  Use the database access client to connect to the database server as the root user:

    .. code-block:: console

        $ mysql -u root -p
    ..

#.  Create the guts database:

    .. code-block:: console

        CREATE DATABASE guts;
    ..

#.  Grant proper access to the guts database:

    .. code-block:: console

        mysql> CREATE DATABASE guts;
        mysql> GRANT ALL PRIVILEGES ON guts.* TO 'guts'@'localhost' \
            IDENTIFIED BY 'GUTS_DBPASS';
        mysql> exit;
    ..

Replace GUTS_DBPASS with a suitable password.

#.  Exit the database access client.

#.  Source the admin credentials to gain access to admin-only CLI commands:

    .. code-block:: console

        $ source admin-openrc.sh
    ..

To create the service credentials, complete these steps:

#.  Create the guts user:

    .. code-block:: console

        $ openstack user create --password-prompt guts
        User Password:
        Repeat User Password:
        +----------+----------------------------------+
        | Field    | Value                            |
        +----------+----------------------------------+
        | email    | None                             |
        | enabled  | True                             |
        | id       | 881ab2de4f7941e79504a759a83308be |
        | name     | guts                             |
        | username | guts                             |
        +----------+----------------------------------+
    ..

#.  Add the admin role to the guts user and service project:

    .. code-block:: console

        $ openstack role add --project service --user guts admin
    ..

#.  Create the guts service entity:

    .. code-block:: console

        $ openstack service create --name guts \
          --description "OpenStack Migration Service" migration
        +-------------+----------------------------------+
        | Field       | Value                            |
        +-------------+----------------------------------+
        | description | OpenStack Migration Service      |
        | enabled     | True                             |
        | id          | 1e494c3e22a24baaafcaf777d4d467eb |
        | name        | guts                             |
        | type        | migration                        |
        +-------------+----------------------------------+
    ..

To install and configure guts:

#.  Source the admin credentials to gain access to admin-only CLI commands:

    .. code-block:: console

        SERVICE=guts
        useradd --home-dir "/var/lib/$SERVICE" \
            --create-home \
            --system \
            --shell /bin/false \
            $SERVICE
        #Create essential dirs
        
        mkdir -p /var/log/$SERVICE
        mkdir -p /etc/$SERVICE
        
        #Set ownership of the dirs
        
        chown -R $SERVICE:$SERVICE /var/log/$SERVICE
        chown -R $SERVICE:$SERVICE /var/lib/$SERVICE
        chown $SERVICE:$SERVICE /etc/$SERVICE
        
        git clone https://github.com/aptira/guts.git
        cd $SERVICE
        cp -R $SERVICE/etc/* /etc/$SERVICE/
        pip install –e .
    ..

Edit the /etc/guts/guts.conf file and complete the following actions:

#.  In the [database] section, configure database access:

    .. code-block:: console

        [database]
        ...
        connection = mysql://guts:GUTS_DBPASS@controller/guts
    ..

#.  In the [DEFAULT] and [oslo_messaging_rabbit] sections, configure RabbitMQ message queue access:

    .. code-block:: console

        [DEFAULT]
        ...
        rpc_backend = rabbit
        [oslo_messaging_rabbit]
        ...
        rabbit_host = guts
        rabbit_userid = openstack
        rabbit_password = RABBIT_PASS
    ..

#.  In the [DEFAULT] and [keystone_authtoken] sections, configure Identity service access:

    .. code-block:: console

        [DEFAULT]
        ...
        auth_strategy = keystone
        [keystone_authtoken]
        ...
        auth_uri = http://controller:5000
        auth_url = http://controller:35357
        auth_plugin = password
        project_domain_id = default
        user_domain_id = default
        project_name = service
        username = guts
        password = GUTS_PASS
    ..

#.  Populate the Guts database:

    .. code-block:: console

        su -s /bin/sh -c "guts-manage db sync" guts
    ..

#.  Start guts services

    .. code-block:: console

        guts-api --config-file /etc/guts/guts.conf
        guts-migration --config-file /etc/guts/guts.conf
    ..
