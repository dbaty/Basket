"""Compatibility layer for Python 3."""

import sys
try:
    from urllib import request as urllib
except:
    # Python 2
    import urllib
try:
    import xmlrpclib
except:  # pragma: no cover
    # Python 3
    import xmlrpc.client as xmlrpclib


if sys.version[0] == '3':  # pragma: no cover
    def text(byte_string):
        return str(byte_string, 'utf-8')
else:  # pragma: no cover
    def text(s):
        return s
