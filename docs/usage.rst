=====
Usage
=====

`xdmenu` is a wrapper API for `dmenu`_.  The original use case of `xdmenu` was
to ease the integration of `dmenu` with `Qtile`_, a window manager written in
Python.

.. _dmenu: http://tools.suckless.org/dmenu/
.. _Qtile: http://www.qtile.org

The simplest possible usage of this wrapper is through the :func:`xdmenu.dmenu`
function.  Here is an example usage::

    >>> from xdmenu import dmenu
    >>> dmenu(['foo', 'bar'])  # shows a menu window with choices on one line
    ['bar']                    # the user picked 'bar'
    >>> dmenu(['foo', 'bar'], lines=2)  # shows a menu window with two lines
    ['foo']                             # the user picked 'foo'


.. autofunction:: xdmenu.dmenu
    :noindex:

The :mod:`xdmenu` package also provides the :class:`xdmenu.Dmenu` class.  This
class can be provided with default configuration values to customize the
behavior of `dmenu`.

.. autoclass:: xdmenu.Dmenu
    :noindex:

Run `dmenu` using :meth:`xdmenu.BaseMenu.run` which all child class should have.

.. automethod:: xdmenu.BaseMenu.run
    :noindex:

If you only want to get the command line arguments, simply use
:meth:`xdmenu.BaseMenu.make_cmd`

.. automethod:: xdmenu.BaseMenu.make_cmd
    :noindex:

Since `xdmenu` is intended to be extensible, you can add supported options
using :meth:`xdmenu.BaseMenu.add_arg`

.. automethod:: xdmenu.BaseMenu.add_arg
    :noindex:

`xdmenu` also provides a wrapper for `dmenu2`_.  See :class:`xdmenu.Dmenu2`.

.. _dmenu2: https://bitbucket.org/melek/dmenu2

