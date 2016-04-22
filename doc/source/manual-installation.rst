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

===================
Manual Installation
===================

This section describes how to install and configure the GUTS migration
service, code-named ``guts`` on Ubuntu 14.04.


Prerequisites
~~~~~~~~~~~~~

Assuming that OpenStack core components (Keystone, Glance, Nova, Cinder and
Horizon) and MySQL are up and running on the target cloud platform.

Before you install and configure GUTS migration service, you must create
a database, user credentials, a service entity and API endpoints for GUTS.

1. To create the database, complete these steps:

  * Use the database access client to connect to the database server as
    the ``root`` user:

    .. code-block:: console

        $ mysql -u root -p

  * Create the ``guts`` database:

    .. code-block:: console

        CREATE DATABASE guts;

  * Grant proper access to the ``guts`` database:

    .. code-block:: console

        GRANT ALL PRIVILEGES ON guts.* TO 'guts'@'localhost' \
            IDENTIFIED BY 'GUTS_DBPASS';
        GRANT ALL PRIVILEGES ON guts.* TO 'guts'@'%' \
            IDENTIFIED BY 'GUTS_DBPASS';

    Replace ``GUTS_DBPASS`` with a suitable password.

  * Exit the database access client.

2. Source the admin credentials to gain access to admin-only CLI commands:

    .. code-block:: console

        $ source admin-openrc.sh

3. To create the user credentials, complete these steps:

  * Create the ``guts`` user in OpenStack and choose a secure password for it:

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

  * Add the ``admin`` role to the ``guts`` user on ``service`` project:

    .. code-block:: console

        $ openstack role add --project service --user guts admin

3. Create a service entity in OpenStack for GUTS:

  * Create the ``guts`` service entity:

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

4. To create the service API endpoints, complete these steps:

  * Create GUTS migration service API endpoints:

    .. code-block:: console

       $ openstack endpoint create --region RegionOne \
             migration public http://controller:7000/v1/%\(tenant_id\)s
         +--------------+-----------------------------------------+
         | Field        | Value                                   |
         +--------------+-----------------------------------------+
         | enabled      | True                                    |
         | id           | 03fa2c90153546c295bf30ca86b1344b        |
         | interface    | public                                  |
         | region       | RegionOne                               |
         | region_id    | RegionOne                               |
         | service_id   | ab3bbbef780845a1a283490d281e7fda        |
         | service_name | gus                                     |
         | service_type | migration                               |
         | url          | http://controller:7000/v1/%(tenant_id)s |
         +--------------+-----------------------------------------+
       
       $ openstack endpoint create --region RegionOne \
         migration internal http://controller:7000/v1/%\(tenant_id\)s
         +--------------+-----------------------------------------+
         | Field        | Value                                   |
         +--------------+-----------------------------------------+
         | enabled      | True                                    |
         | id           | 94f684395d1b41068c70e4ecb11364b2        |
         | interface    | internal                                |
         | region       | RegionOne                               |
         | region_id    | RegionOne                               |
         | service_id   | ab3bbbef780845a1a283490d281e7fda        |
         | service_name | guts                                    |
         | service_type | migration                               |
         | url          | http://controller:7000/v1/%(tenant_id)s |
         +--------------+-----------------------------------------+
       
       $ openstack endpoint create --region RegionOne \
         migration admin http://controller:7000/v1/%\(tenant_id\)s
         +--------------+-----------------------------------------+
         | Field        | Value                                   |
         +--------------+-----------------------------------------+
         | enabled      | True                                    |
         | id           | 4511c28a0f9840c78bacb25f10f62c98        |
         | interface    | admin                                   |
         | region       | RegionOne                               |
         | region_id    | RegionOne                               |
         | service_id   | ab3bbbef780845a1a283490d281e7fda        |
         | service_name | guts                                    |
         | service_type | migration                               |
         | url          | http://controller:7000/v1/%(tenant_id)s |
         +--------------+-----------------------------------------+

Install and configure GUTS components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create user and essential directories for GUTS:

    .. code-block:: console

        $ SERVICE=guts
        $ useradd --home-dir "/var/lib/$SERVICE" \
            --create-home \
            --system \
            --shell /bin/false \
            $SERVICE

    Create directories:

    .. code-block:: console
    
        $ mkdir -p /var/log/$SERVICE
        $ mkdir -p /etc/$SERVICE
        
    Set ownership of the directories:

    .. code-block:: console
    
        $ chown -R $SERVICE:$SERVICE /var/log/$SERVICE
        $ chown -R $SERVICE:$SERVICE /var/lib/$SERVICE
        $ chown $SERVICE:$SERVICE /etc/$SERVICE

2. Clone GUTS repository:

    .. code-block:: console

        $ git clone https://github.com/aptira/guts.git

3. Install GUTS components:

    .. code-block:: console

        $ cd $SERVICE
        $ cp -R $SERVICE/etc/* /etc/$SERVICE/
        $ pip install -e .

4. Configure GUTS by editing the ``/etc/guts/guts.conf`` file:

  * In the ``[database]`` section, configure database access:

    .. code-block:: console

        [database]
        connection = mysql://guts:GUTS_DBPASS@controller/guts

    Replace ``controller`` above with the actual hostname or IP address of your
    OpenStack controller node.

  * In the ``[DEFAULT]`` and ``[oslo_messaging_rabbit]`` sections, configure
    RabbitMQ message queue access:

    .. code-block:: console

        [DEFAULT]
        rpc_backend = rabbit

        [oslo_messaging_rabbit]
        rabbit_host = guts
        rabbit_userid = openstack
        rabbit_password = RABBIT_PASS

    Replace ``RABBIT_PASS`` above with actual password for RabbitMQ service.

  * In the ``[DEFAULT]`` and ``[keystone_authtoken]`` sections, configure
    OpenStack Identity service access:

    .. code-block:: console

        [DEFAULT]
        auth_strategy = keystone

        [keystone_authtoken]
        auth_uri = http://controller:5000
        auth_url = http://controller:35357
        auth_plugin = password
        project_domain_id = default
        user_domain_id = default
        project_name = service
        username = guts
        password = GUTS_PASS

    Replace ``GUTS_PASS`` above with actual password set for ``guts`` user when
    it is created in previous step.

5. Perform database synchronisation:

  * Populate the ``guts`` database:

    .. code-block:: console

        $ su -s /bin/sh -c "guts-manage db sync" guts
    ..

6. Start GUTS services:

  * Start ``guts-api``, ``guts-scheduler`` and ``guts-migration`` services:

    .. code-block:: console

        $ guts-api --config-file /etc/guts/guts.conf
        $ guts-scheduler --config-file /etc/guts/guts.conf
        $ guts-migration --config-file /etc/guts/guts.conf


Configure GUTS dashboard
~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone ``guts-dashboard`` repository:

    .. code-block:: console

        $ git clone https://github.com/aptira/guts-dashboard.git

2. Install the OpenStack Dashboard plugin for GUTS:

    .. code-block:: console

        $ cd guts-dashboard
        $ pip install -e .

3. Enable dashboard plugin in Horizon (For devstack environment):

    .. code-block:: console

        $ cd /opt/stack/horizon/openstack_dashboard/local/enabled
        $ ln -s /opt/stack/guts-dashboard/_50_guts.py.example _50_guts.py

4. Restart web server to reload the new configuration:

    .. code-block:: console

        $ service apache2 restart

After finishing these steps, you should be able to see GUTS user interface
appearing in Horizon. For more information about GUTS dashboard, please refer
to its `document <http://guts-dashboard.readthedocs.org>`_.
