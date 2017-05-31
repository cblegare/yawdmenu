=====
Usage
=====

The simplest possible usage of this wrapper is through the :func:`xdmenu.dmenu`
function.

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


