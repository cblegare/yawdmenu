#!/usr/bin/python3.5
# coding: utf8


"""Package main definition."""


from __future__ import absolute_import

from pkg_resources import get_distribution, DistributionNotFound


__project__ = 'xdmenu'
__version__ = None  # required for initial installation

try:
    distribution = get_distribution(__project__)
    __version__ = distribution.version

except DistributionNotFound:
    # This will happen if the package is not installed.
    # For more informations about development installation, read about
    # the 'develop' setup.py command or the '--editable' pip option.
    # Note that development installations may break other packages from
    # the same implicit namespace
    # (see https://github.com/pypa/packaging-problems/issues/12)
    __version__ = '(local)'
else:
    pass


class DmenuError(Exception):
    """
    Something went wrong with dmenu.
    """
    def __init__(self, args, stderr):
        msg = ('The provided dmenu command could not be used: '
               '{!s} {!s}'.format(args, stderr))
        super(DmenuError, self).__init__(msg)


class DmenuUsageError(DmenuError):
    """
    Some arguments to dmenu where invalid.
    """

    def __init__(self, args, stderr):
        msg = ('This version of dmenu does not support your usage: '
               '{!s} {!s}'.format(args, stderr))
        super(DmenuUsageError, self).__init__(msg)


from xdmenu.dmenu import dmenu, Dmenu

__all__ = ['dmenu', 'Dmenu', 'DmenuError', 'DmenuUsageError']
