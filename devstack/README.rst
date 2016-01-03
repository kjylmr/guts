====================
Enabling in Devstack
====================

#. Download DevStack_::

    git clone https://git.openstack.org/openstack-dev/devstack
    cd devstack

#. Edit local.conf to enable guts devstack plugin::

     > cat local.conf
     [[local|localrc]]
     enable_plugin guts https://dev.aptira.com/bharat/guts

#. Install DevStack::

    ./stack.sh
