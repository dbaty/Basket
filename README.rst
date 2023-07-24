**Basket does not work anymore. It will not be fixed, because it is
not supported anymore. You should switch to pip.** ``pip`` is
standard and comes with a lot more features and does not have many of
the limitations of Basket.

- Basket uses the XML-RPC API from PyPI, which is (or will soon be)
  `deprecated <https://warehouse.pypa.io/api-reference/xml-rpc.html>`_.
  Actually, some of the functions that Basket uses are not
  implemented anymore by the API. In other words, **Basket does not work
  anymore**.

- Basket does not support "version qualifiers" like ``Django>=4.0``.
  It just downloads the most recent version, which may not be
  compatible with other dependencies. Also, by ignoring ``==``
  qualifiers, Basket is incapable of setting up a reproducible
  environment. ``pip`` being the de-facto package install for Python,
  it has finer dependency version control.

- Basket only downloads source distributions. ``pip`` download wheels
  if available.

- Basket only downloads from PyPI and cannot download packages that
  are hosted elsewhere. ``pip`` can.

- Basket downloads all optional requirements. This was a feature, but
  that's not necessarily what you want. ``pip`` does what you tell it
  to do.


Migration guide from Basket to Pip
==================================

Important: if you're still using Python 2, be sure to use the latest
version of ``pip`` that is compatible with Python 2, which seems to be
version 20.3.4.

The following instructions are for Linux but commands are similar on
Windows.

Before anything, you must create a new directory that will contain
packages::

    $ export PACKAGE_DIRECTORY=/home/you/packages
    $ mkdir $PACKAGE_DIRECTORY

How to download packages::

    $ pip download --dest $PACKAGE_DIRECTORY Django

How to install packages::

    $ pip install --no-index --find-links=$PACKAGE_DIRECTORY Django


Legacy description
==================

Basket is a small command-line utility that downloads Python packages
from a (real) PyPI server and store them in a single place so that
they can be found by ``easy_install`` or ``pip`` when offline.

I often work offline (typically in the train). It is not unusal then
to have to create a virtual environment and fill it with the Python
packages I need. Without an Internet connection, I could copy Python
packages from an environment to another, but this is a bit
cumbersome. I need a local PyPI repository. Basket allows me to build
and maintain such a repository.

Basket is not a PyPI mirror. It is not a server: you cannot register
or upload packages. It does not install Python packages in a Python
installation or a virtual environment.

For further details, see the documentation at `<http://packages.python.org/Basket>`_ (or in the ``docs/`` folder in the source).
