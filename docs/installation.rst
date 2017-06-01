.. highlight:: shell

============
Installation
============

`xdmenu` uses and needs an implementation of `dmenu`.  This means a command
line program that reads lines from *stdin*, presents these lines to the user as
a menu and prints the chosen lines to *stdout*.

dmenu_
    *dmenu is a dynamic menu for X, originally designed for dwm. It manages
    large numbers of user-defined menu items efficiently.*

dmenu2_
    *dmenu2 is the fork of original dmenu - an efficient dynamic menu for X,
    patched with XFT, quiet, x & y, token, fuzzy matching, follow focus, tab
    nav, filter.*

    *Added option to set screen on which dmenu apperars, as long as opacity,
    window class and window name. Also allows to dim screen with selected color
    and opacity while dmenu2 is running.*

    *Added underline color and height. (options -uc and -uh)*

Rofi_
    *Rofi, like dmenu, will provide the user with a textual list of options
    where one or more can be selected. This can either be, running an
    application, selecting a window or options provided by an external script.*

.. _dmenu: http://tools.suckless.org/dmenu/
.. _dmenu2: https://bitbucket.org/melek/dmenu2
.. _Rofi: https://davedavenport.github.io/rofi/


Stable release
--------------

To install `xdmenu`, run this command in your terminal:

.. code-block:: console

    $ pip install xdmenu

This is the preferred method to install `xdmenu`, as it will always install the
most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for `xdmenu` can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/cblegare/xdmenu

Or download the `tarball`_:

.. code-block:: console

    $ curl -OL https://github.com/cblegare/xdmenu/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/cblegare/xdmenu
.. _tarball: https://github.com/cblegare/xdmenu/tarball/master
