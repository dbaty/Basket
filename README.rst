Basket - a local static PyPI repository builder
===============================================

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


Usage
=====

You need Python 2.7 to run Basket. It may work with prior versions of
Python 2 and/or Python 3 but this has not been tested (yet).

1. Install Basket::

       $ easy_install Basket

   or::

       $ pip install Basket

2. Initialize your Basket repository::

       $ basket init
       Repository has been created: ~/.basket

   This will create a ``.basket/`` directory in your home folder. If
   this location is not appropriate, you may configure it by setting a
   ``BASKET_ROOT`` environment variable. If the directory already
   exists, an error message will be printed.

3. Download one or more packages::

       $ basket download docutils
       Added docutils 0.8.1.
       $ basket download nose coverage
       Added coverage 3.5.1.
       Added nose 1.1.2.

   Basket searches for the name of the package so the case does not
   matter::

       $ basket download MySql-pYthon
       Added MySQL-python 1.2.3.

   If you already have the latest version of the requested package,
   Basket will not download it again. If there is a more recent
   version, Basket will download it but will also keep the old
   one. This is a feature: if you want to remove old versions, use the
   ``prune`` command (see below).

   Note that Basket also downloads requirements::

       $ basket download sphinx
       Added Sphinx 1.1.2.
         -> requires: Pygments, Jinja2, docutils
       Added Pygments 1.4.
       Added Jinja2 2.6.
         -> requires: Babel
       docutils is already up to date (0.8.1).
       Added Babel 0.9.6.

   See the `Limitations and features`_ section below for further
   details about how Basket handle requirements.

4. List all downloaded packages::

       $ basket list
       Babel 0.9.6
       coverage 3.5.1
       docutils 0.8.1
       Jinja2 2.6
       MySQL-python 1.2.3
       nose 1.1.2
       Pygments 1.4
       Sphinx 1.1.2

   Or only one or more specific packages::

       $ basket list docutils
       docutils 0.8.1
       $ basket list nose coverage
       coverage 3.5.1
       nose 1.1.2

5. You probably want to update packages regularly. The following will
   download the latest version of each existing package if you do not
   have it already::

       $ basket update docutils
       docutils is already up to date (0.8.1).

   Ok, we have the latest versions. Let's mess with the repository to
   make it think that we have an old version of ``docutils``::

       $ mv ~/.basket/docutils-0.8.1.tar.gz ~/.basket/docutils-0.7.tar.gz
       $ basket list docutils
       docutils 0.7

   And ask again::

       $ basket update docutils
       Added docutils 0.8.1.

   As indicated above for the ``download`` command, old versions are
   kept alongside the latest one. This is a feature.

   ::

       $ basket list docutils
       docutils 0.7
       docutils 0.8.1

   You may also update only a particular package or a set of packages::

       $ basket update Sphinx
       Sphinx is already up to date (1.1.2).
       $ basket update nose coverage
       coverage is already up to date (3.5.1).
       nose is already up to date (1.1.2).

   Usually, though, you would ask for an update of all downloaded packages::

       $ basket update
       Babel is already up to date (0.9.6).
       coverage is already up to date (3.5.1).
       docutils is already up to date (0.8.1).
       Jinja2 is already up to date (2.6).
       MySQL-python is already up to date (1.2.3).
       nose is already up to date (1.1.2).
       Pygments is already up to date (1.4).
       Sphinx is already up to date (1.1.2).

6. If you wish to keep only the latest version of each package, use
   the ``prune`` command::

       $ basket list docutils
       docutils 0.7
       docutils 0.8.1
       $ basket prune docutils
       Removed docutils 0.7 (kept 0.8.1).

   You may do the same thing on all downloaded packages::

       $ basket prune
       Babel has only one version. Nothing to prune.
       coverage has only one version. Nothing to prune.
       docutils has only one version. Nothing to prune.
       Jinja2 has only one version. Nothing to prune.
       MySQL-python has only one version. Nothing to prune.
       nose has only one version. Nothing to prune.
       Pygments has only one version. Nothing to prune.
       Sphinx has only one version. Nothing to prune.

   Of course, it would be wiser to update downloaded packages before
   pruning anything. Otherwise, you may end up keeping only your
   latest *downloaded* packages instead of the latest *released*
   packages.

Obviously, all commands above (except ``list``) require an Internet
connection. The point of Basket is that if you are offline, you can
install your preferred packages from your Basket repository::

       $ easy_install -f ~/.basket -H None pyramid

Or if you prefer Pip::

       $ pip install --no-index -f file:///path/to/.basket pyramid

Running Basket without any argument, with wrong arguments or with the
``help`` will print an helpful message that describe each command.


Commands
========

``help``
  Display an helpful message with the syntax of each command.

``init``
  Initialize a new repository named ``.basket`` in your home folder
  (unless a ``BASKET_ROOT`` environment variable is set, in which case
  its value is used as the path to the repository)

``download <package1> <package2> ...``
  Download one or more packages.

``list [<package1> <package2> ...]``
  List all downloaded packages (or only the requested ones).

``prune [<package1> <package2> ...]``
  Keep only the latest version of each downloaded package (or only the
  requested ones).

``update [<package1> <package2> ...]``
  Download latest version of each downloaded package (or only the
  requested ones) if we do not already have it.


Limitations and features
========================

Basket downloads source distributions only. That may or may not cause
issues for certain packages on certain platforms.

When looking at requirements, Basket only cares about the name of the
package, ignoring any particular version requirements (e.g.
"docutils>=0.8.1") and thus always downloading the latest version.
This may be a problem for packages that explictly require a version
that is not the latest.

Also, Basket downloads optional requirements. This is a feature.


Meta
====

Basket is hosted on GitHub: `<https://github.com/dbaty/basket>`_. Feel
free to report bugs and contribute there.

Basket is written by Damien Baty and is licenced under the 3-clause
BSD license, a copy of which is included in the source.