====
GUTS
====

A Workload migration engine designed to automatically move
existing workloads and virtual machines from various previous
generation virtualisation platforms on to OpenStack.

Guts provides seamless and fully automated migration for both Linux or Windows
virtual machines to OpenStack infrastructure.

Guts can be integrated with an existing OpenStack infrastructure
by following `installation instructions <http://guts.readthedocs.org/en/latest/manual-installation.html>`_.

OpenStack Guts is distributed under the terms of the Apache
License, Version 2.0. The full terms and conditions of this
license are detailed in the LICENSE file.

* Reference: https://aptira.com/guts
* GitHub: https://github.com/aptira/guts

Architecture
------------

GUTS primarily consists of a set of Python daemons, though
it requires and integrates with a number of native system
components for databases, messaging and miagaration
capabilities.

GUTS architecture diagram looks like::

                                                                          +-----------------+
                                                                          |                 |
                                                                          |      VMWare     |
                                                                       +->|Source Hypervisor|
 +-----------+                                      +---------------+  |  |                 |
 |           |                         +------+     |               |  |  +-----------------+
 |Guts Client+--+                      |      |  +->|guts-migration +--+
 |           |  |   +--------------+   |      |  |  |               |
 +-----------+  +-->|              |   |      +--+  +---------------+
                    |   guts-api   +-->| AMQP |
 +-----------+  +-->|              |   |      +--+  +---------------+
 |           |  |   +--------------+   |      |  |  |               |
 |  Horizon  +--+                      |      |  +->|guts-migration +--+
 |           |                         +------+     |               |  |  +-----------------+
 +-----------+                                      +---------------+  |  |                 |
                                                                       +->|     Hyper-V     |
                                                                          |Source Hypervisor|
                                                                          |                 |
                                                                          +-----------------+


guts-api:

* Accepts and responds to end user migration API calls.
* Exposes RESTful APIs on the port 7000

guts-migration:

* A worker daemon that migrates VMs from source hypervisor to OpenStack
* Also communicates with Glance, Nova and Neutron to create VM on OpenStack

Other Components
----------------

Guts Documentation:

* Documentation for GUTS
* http://guts.readthedocs.org/en/latest/

Guts Client:

* Command line interface to interact with guts-api
* https://github.com/aptira/python-gutsclient.git

Guts Dashboard:

* Guts Dashboard is an extension for OpenStack Dashboard which provides UI for guts.
* https://github.com/aptira/guts-dashboard.git

Devstack Plugin:

* Guts also provides devstack plugin, which provides an automated way to deploy Guts through devstack.
* https://github.com/aptira/guts/tree/master/devstack

Guts demo:

* A demo session recording, explaining GUTS command line tools
* https://asciinema.org/a/1nwd6vpvm93ajaik6xl9y834w

Guts on Horizon:

* Screenshots of dashboard plugin which explains guts workflow as part of horizon
* http://guts-dashboard.readthedocs.io/en/latest/user-guide.html
