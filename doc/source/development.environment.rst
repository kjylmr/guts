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

=============================================
Setting up a Guts development environment
=============================================

This document describes getting the source from guts's `Git repository`_
for development purposes.

Currently Guts is only installable from source and no packaged binary is available.

.. _`Git Repository`: http://git.openstack.org/cgit/openstack/keystone


Prerequisites
=============

This document assumes you are using Ubuntu

And that you have the following tools available on your system:

- Python_ 2.7 and 3.4
- git_
- setuptools_
- pip_
- msgfmt (part of the gettext package)

.. _Python: http://www.python.org/
.. _git: http://git-scm.com/
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _tox: https://pypi.python.org/pypi/tox

Getting the latest code
=======================

Make a clone of the code from our `Git repository`:

.. code-block:: bash

    $ git clone https://github.com/aptira/guts.git

When that is complete, you can:

.. code-block:: bash

    $ cd guts

Installing dependencies
=======================

Guts maintains two lists of dependencies::

    requirements.txt
    test-requirements.txt

The first is the list of dependencies needed for running guts, the second list includes dependencies used for active development and testing of guts itself.

These dependencies can be installed from PyPi_ using the Python tool pip_.

.. _PyPi: http://pypi.python.org/
.. _pip: http://pypi.python.org/pypi/pip

However, your system *may* need additional dependencies that `pip` (and by
extension, PyPi) cannot satisfy. These dependencies should be installed
prior to using `pip`, and the installation method may vary depending on
your platform.
