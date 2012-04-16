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