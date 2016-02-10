Building Docs
=============

Developer documentation is generated using Sphinx. To build this documentation,
run the following from inside `doc` directory of the root of the repository::

    $ cd doc && make html

The documentation will be built at ``doc/build/``.

View them on http://localhost:8000 locally after hitting::

    $ cd doc/build/html && python -m SimpleHTTPServer
