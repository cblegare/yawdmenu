#!/usr/bin/python3.5
# coding: utf8


"""Package main definition."""


from __future__ import absolute_import

from collections import OrderedDict
import subprocess

from pkg_resources import get_distribution, DistributionNotFound
import six


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


__all__ = ['dmenu',
           'BaseMenu',
           'Dmenu',
           'Dmenu2',
           'DmenuError',
           'DmenuUsageError']


def dmenu(choices, dmenu=None, **kwargs):
    """
    Run `dmenu` with configuration provided in ``**kwargs``.

    Args:
        choices (list): Choices to put in menu
        dmenu (xdmenu.BaseMenu): A :class:`xdmenu.BaseMenu` instance to use.
            If not provided, a default one will be created.
        \*\*kwargs: Any of the supported argument added via
            :meth:`xdmenu.BaseMenu.add_arg`.

    Returns:
        list: All the choices made by the user.

    See Also:
        :meth:`xdmenu.BaseMenu.run`
    """
    dmenu_instance = dmenu or Dmenu(**kwargs)
    return dmenu_instance.run(choices)


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


class BaseMenu(object):
    def __init__(self, dmenu=None, proc_runner=None, **kwargs):
        """
        An extensible dmenu wrapper.

        Args:
            dmenu (str): dmenu executable to use.
            proc_runner (Callable[[list, list], str]): a function that calls
               dmenu as a subprocess and returns the output.  This defaults to
               a simple call to :class:`subprocess.Popen`.
            \*\*kwargs: See :meth:`xdmenu.BaseMenu.configure`
        """
        self._dmenu_args = OrderedDict()
        self._dmenu_config = OrderedDict()
        self._run_dmenu_process = proc_runner or _run_dmenu_process
        bin = dmenu or 'dmenu'
        self.add_arg('dmenu', _dmenu, default=bin)
        self.configure(**kwargs)

    def configure(self, **kwargs):
        """
        Set a value to any of the supported argument added.

        See Also:
            :meth:`xdmenu.BaseMenu.add_arg`.

        Args:
            \*\*kwargs: Keywords are mapped to the name of the argument, and
                the value is kept for a future call to dmenu.
        """
        self._dmenu_config.update(kwargs)

    def make_cmd(self, **kwargs):
        """
        Build the list of command line arguments to dmenu.

        Args:
            \*\*kwargs: See :meth:`xdmenu.BaseMenu.configure`, except that
                values are no kept for a later call to dmenu

        Returns:
            list: List of command parts ready to sead to
                :class:`subprocess.Popen`

        Examples:

            >>> menu = Dmenu()
            >>> menu.make_cmd()
            ['dmenu']
            >>> menu.make_cmd(bottom=True)
            ['dmenu', '-b']
            >>> menu.make_cmd(lines=2, prompt='-> ',)
            ['dmenu', '-l', '2', '-p', '-> ']
        """
        config = self._dmenu_config.copy()
        config.update(kwargs)
        cmd = []
        for name, value in six.iteritems(config):
            arg_converter = self._dmenu_args[name]
            cli_arg_list = arg_converter(value)
            cmd.extend(cli_arg_list)
        return cmd

    def version(self, dmenu=None):
        """
        Return dmenu version string.

        Args:
            dmenu (str): dmenu executable to use.  Defaults to the one
                configured in `self`.

        Returns:
            str: The configured dmenu's version string
        """
        cmd = [dmenu or self._dmenu_config['dmenu'], '-v']
        version = self._run_dmenu_process(cmd)[0]
        return version

    def run(self, choices, **kwargs):
        """
        Args:
            choices (list): Choices to put in menu
            \*\*kwargs: See :meth:`xdmenu.BaseMenu.configure`, except that
                values are no kept for a later call to dmenu

        Examples:

            >>> # We mock the _run_dmenu_process function for this example
            >>> # to be runnable even if dmenu is not installed
            >>> # The mock mimics a user choosing the first choice
            >>> m = Dmenu(proc_runner=_mock_dmenu_process)
            >>> m.run(['foo', 'bar'])
            ['foo']

        Returns:
            list: All the choices made by the user.  In order to have multiple
            results, a custom build of `dmenu` may be required since the
            original version may not support selecting many items.
        """
        choices = choices or []
        cmd = self.make_cmd(**kwargs)
        choice = self._run_dmenu_process(cmd, input_lines=choices)
        return choice

    def add_arg(self, name, converter, default=None):
        """
        Extend this wrapper by registering a new dmenu argument.

        You can also use this to change the behavior of existing arguments.

        Args:
            name (str): The name of the supported keyword argument for this
                wrapper.

            converter (Callable[[Any], Iterable]): A function that converts the
                configured value to a list of command line arguments to dmenu.

            default (Optional[Any]): The default configured value.

        Examples:

            Let's wrap the usage of a `-foo` argument that a dmenu fork could
            possibly support.

            >>> def to_bottom(arg):
            ...     return ['-foo'] if arg else []
            >>> menu = Dmenu()
            >>> menu.add_arg('foo', to_bottom, default=False)
            >>> menu.make_cmd()
            ['dmenu']
            >>> menu.make_cmd(foo=True)
            ['dmenu', '-foo']
        """
        self._dmenu_args[name] = converter
        self._dmenu_config.setdefault(name, default)


class Dmenu(BaseMenu):
    def __init__(self, proc_runner=None, **kwargs):
        """
        An extensible dmenu wrapper that already supports all usual arguments.

        Args:
            dmenu (str): See :meth:`xdmenu.BaseMenu`

            proc_runner (Callable[[list, list], str]): See
                :meth:`xdmenu.BaseMenu`

            bottom (bool): dmenu appears at the bottom of the screen.
                Equivalent for the ``-b`` command line option of dmenu.

            grab (bool): dmenu grabs the keyboard before reading stdin.  This
                is faster, but will lock up X until stdin reaches end-of-file.
                Equivalent for the ``-f`` command line option of dmenu.

            insensitive (bool): dmenu matches menu items case insensitively.
                Equivalent for the ``-i`` command line option of dmenu.

            lines (int): dmenu lists items vertically, with the given number of
                lines.  Equivalent for the ``-l`` command line option of dmenu.

            monitor (int): dmenu is displayed on the monitor number supplied.
                Monitor numbers are starting from 0.  Equivalent for the ``-m``
                command line option of dmenu.

            prompt (str): defines the prompt to be displayed to the left of the
                input field.  Equivalent for the ``-p`` command line option of
                dmenu.

            font (str): defines the font or font set used.  Equivalent for the
                ``-fn`` command line option of dmenu.

            normal_bg_color (str): defines the normal background color.  #RGB,
                #RRGGBB, and X color names are supported.  Equivalent for the
                ``-nb`` command line option of dmenu.

            normal_fg_color (str): defines the normal foreground color.
                Equivalent for the ``-nf`` command line option of dmenu.

            selected_bg_color (str): defines the selected background color.
                Equivalent for the ``-sb`` command line option of dmenu.

            selected_fg_color (str): defines the selected foreground color.
                Equivalent for the ``-sf`` command line option of dmenu.

            windowid (str): embed into windowid.

        """
        super(self.__class__, self).__init__(proc_runner=proc_runner, **kwargs)
        self.add_arg('bottom', _bottom)
        self.add_arg('grab', _grab)
        self.add_arg('insensitive', _insensitive)
        self.add_arg('lines', _lines)
        self.add_arg('monitor', _monitor)
        self.add_arg('prompt', _prompt)
        self.add_arg('font', _font)
        self.add_arg('normal_bg_color', _normal_bg_color)
        self.add_arg('normal_fg_color', _normal_fg_color)
        self.add_arg('selected_bg_color', _selected_bg_color)
        self.add_arg('selected_fg_color', _selected_fg_color)
        self.add_arg('windowid', _windowid)


class Dmenu2(Dmenu):
    def __init__(self, proc_runner=None, **kwargs):
        """
        A wrapper for dmenu2_.

        This wrapper also supports all of :class:`xdmenu.Dmenu` arguments in
        addition to the ones below.

        .. _dmenu2: https://bitbucket.org/melek/dmenu2

        Args:
            dmenu (str): See :meth:`xdmenu.BaseMenu`

            proc_runner (Callable[[list, list], str]): See
                :meth:`xdmenu.BaseMenu`

            filter (bool): activates filter mode. All matching items currently
                shown in the list will be selected, starting with the item that
                is highlighted and wrapping around to the beginning of the
                list. Equivalent for the ``-r`` command line option of dmenu2.

            fuzzy (bool): dmenu uses fuzzy matching. It matches items that have
                all characters entered, in sequence they are entered, but there
                may be any number of characters between matched characters.
                For example it takes ``txt`` makes it to ``*t*x*t`` glob
                pattern and checks if it matches. Equivalent for the ``-z``
                command line option of dmenu2.

            token (bool): dmenu uses space-separated tokens to match menu
                items. Using this overrides `fuzzy` option. Equivalent for the
                ``-t`` command line option of dmenu2.

            mask (bool): dmenu masks input with asterisk characters (*).
                Equivalent for the ``-mask`` command line option of dmenu2.

            screen (int): dmenu apears on the specified screen number. Number
                given corresponds to screen number in X configuration.
                Equivalent for the ``-s`` command line option of dmenu2.

            window_name (str): defines window name for dmenu. Defaults to
                "dmenu". Equivalent for the ``-name`` command line option of
                dmenu2.

            window_class (str): defines window class for dmenu. Defaults to
                "Dmenu". Equivalent for the ``-class`` command line option of
                dmenu2.

            opacity (float): defines window opacity for dmenu. Defaults to 1.0.
                Equivalent for the ``-o`` command line option of dmenu2.

            dim (float): enables screen dimming when dmenu appers. Takes dim
                opacity as argument. Equivalent for the ``-dim`` command line
                option of dmenu2.

            dim_color (str): defines color of screen dimming. Active only when
                -dim in effect. Defautls to black (#000000). Equivalent for the
                ``-dc`` command line option of dmenu2.

            height (int): defines the height of the bar in pixels. Equivalent
                for the ``-h`` command line option of dmenu2.

            xoffset (int): defines the offset from the left border of the
                screen. Equivalent for the ``-x`` command line option of
                dmenu2.

            yoffset (int): defines the offset from the top border of the
                screen. Equivalent for the ``-y`` command line option of
                dmenu2.

            width (int): defines the desired menu window width. Equivalent for
                the ``-w`` command line option of dmenu2.
        """
        super(self.__class__, self).__init__(proc_runner=proc_runner, **kwargs)
        self.add_arg('filter', _filter)
        self.add_arg('fuzzy', _fuzzy)
        self.add_arg('token', _token)
        self.add_arg('mask', _mask)
        self.add_arg('screen', _screen)
        self.add_arg('window_name', _window_name)
        self.add_arg('window_class', _window_class)
        self.add_arg('opacity', _opacity)
        self.add_arg('dim', _dim)
        self.add_arg('dim_color', _dim_color)
        self.add_arg('height', _height)
        self.add_arg('xoffset', _xoffset)
        self.add_arg('yoffset', _yoffset)
        self.add_arg('width', _width)


def _run_dmenu_process(cmd, input_lines=None):
    try:
        proc = subprocess.Popen(cmd,
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                universal_newlines=True)

        stdout, stderr = proc.communicate(input='\n'.join(input_lines))

        if 'usage' in stderr and proc.wait() != 0:
            raise DmenuUsageError(cmd, stderr)

        output = stdout.strip() or ''
        return output.splitlines()
    except OSError as err:
        # something went wrong when starting the process
        six.raise_from(DmenuError(cmd), err)


def _mock_dmenu_process(cmd, input_lines=None):
    # We assert to be called only with 'dmenu' for the purpose
    # of this example.
    assert cmd == ['dmenu']
    # this one will always return the first line if possible
    return [input_lines[0]] if input_lines else []


def _dmenu(arg=None):
    """
    Args:
        arg (str): dmenu executable to use

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _dmenu()
        ['dmenu']
        >>> _dmenu('j4-dmenu-desktop')
        ['j4-dmenu-desktop']
    """
    return [arg] if arg else ['dmenu']


def _bottom(arg=None):
    """
    Args:
        arg (bool): dmenu appears at the bottom of the screen.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _bottom()
        []
        >>> _bottom(True)
        ['-b']
        >>> _bottom('evaluates to True')
        ['-b']
        >>> _bottom(None)
        []
        >>> _bottom(False)
        []
    """
    return ['-b'] if arg else []


def _grab(arg=None):
    """
    Args:
        arg (bool): dmenu grabs the keyboard before reading stdin.  This is
            faster, but will lock up X until stdin reaches end-of-file.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _grab()
        []
        >>> _grab(True)
        ['-f']
        >>> _grab('evaluates to True')
        ['-f']
        >>> _grab(None)
        []
        >>> _grab(False)
        []
    """
    return ['-f'] if arg else []


def _insensitive(arg=None):
    """
    Args:
        arg (bool): dmenu matches menu items case insensitively.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _insensitive()
        []
        >>> _insensitive(True)
        ['-i']
        >>> _insensitive('evaluates to True')
        ['-i']
        >>> _insensitive(None)
        []
        >>> _insensitive(False)
        []
    """
    return ['-i'] if arg else []


def _lines(arg=None):
    """
    Args:
        arg (int): dmenu lists items vertically, with the given number of
            lines.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _lines()
        []
        >>> _lines(1)
        ['-l', '1']
        >>> _lines('2')
        ['-l', '2']
        >>> _lines('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-l', str(int(arg))] if arg is not None else []


def _monitor(arg=None):
    """
    Args:
        arg (int): dmenu is displayed on the monitor number supplied.
            Monitor numbers are starting from 0.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _monitor()
        []
        >>> _monitor(1)
        ['-m', '1']
        >>> _monitor('2')
        ['-m', '2']
        >>> _monitor('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-m', str(int(arg))] if arg is not None else []


def _prompt(arg=None):
    """
    Args:
        arg (str): defines the prompt to be displayed to the left of the
            input field.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _prompt()
        []
        >>> _prompt('>')
        ['-p', '>']
    """
    return ['-p', str(arg)] if arg is not None else []


def _font(arg=None):
    """
    Args:
        arg (str): defines the font or font set used.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _font()
        []
        >>> _font('freetype')
        ['-fn', 'freetype']
    """
    return ['-fn', str(arg)] if arg is not None else []


def _normal_bg_color(arg=None):
    """
    Args:
        arg (str): defines the normal background color. #RGB, #RRGGBB, and X
            color names are supported.

    Returns:
        list: command line arguments to use with dmenu

    See Also:
        https://en.wikipedia.org/wiki/X11_color_names

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _normal_bg_color()
        []
        >>> _normal_bg_color('#008')
        ['-nb', '#008']
        >>> _normal_bg_color('#00008B')
        ['-nb', '#00008B']
        >>> _normal_bg_color('Dark Blue')
        ['-nb', 'Dark Blue']
    """
    return ['-nb', str(arg)] if arg is not None else []


def _normal_fg_color(arg=None):
    """
    Args:
        arg (str): defines the normal foreground color. #RGB, #RRGGBB, and X
            color names are supported.

    Returns:
        list: command line arguments to use with dmenu

    See Also:
        https://en.wikipedia.org/wiki/X11_color_names

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _normal_fg_color()
        []
        >>> _normal_fg_color('#008')
        ['-nf', '#008']
        >>> _normal_fg_color('#00008B')
        ['-nf', '#00008B']
        >>> _normal_fg_color('Dark Blue')
        ['-nf', 'Dark Blue']
    """
    return ['-nf', str(arg)] if arg is not None else []


def _selected_bg_color(arg=None):
    """
    Args:
        arg (str): defines the selected background color. #RGB, #RRGGBB, and X
            color names are supported.

    Returns:
        list: command line arguments to use with dmenu

    See Also:
        https://en.wikipedia.org/wiki/X11_color_names

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _selected_bg_color()
        []
        >>> _selected_bg_color('#008')
        ['-sb', '#008']
        >>> _selected_bg_color('#00008B')
        ['-sb', '#00008B']
        >>> _selected_bg_color('Dark Blue')
        ['-sb', 'Dark Blue']
    """
    return ['-sb', str(arg)] if arg is not None else []


def _selected_fg_color(arg=None):
    """
    Args:
        arg (str): defines the selected foreground color. #RGB, #RRGGBB, and X
            color names are supported.

    Returns:
        list: command line arguments to use with dmenu

    See Also:
        https://en.wikipedia.org/wiki/X11_color_names

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _selected_fg_color()
        []
        >>> _selected_fg_color('#008')
        ['-sf', '#008']
        >>> _selected_fg_color('#00008B')
        ['-sf', '#00008B']
        >>> _selected_fg_color('Dark Blue')
        ['-sf', 'Dark Blue']
    """
    return ['-sf', str(arg)] if arg is not None else []


def _windowid(arg=None):
    """
    Args:
        arg: embed into windowid.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _windowid()
        []
        >>> _windowid('my window')
        ['-w', 'my window']
    """
    return ['-w', str(arg)] if arg is not None else []


def _filter(arg=None):
    """
    Supported by some patches.

    Args:
        arg (bool): activates filter mode. All matching items currently shown
            in the list will be selected, starting with the item that is
            highlighted and wrapping around to the beginning of the list.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _filter()
        []
        >>> _filter(True)
        ['-r']
        >>> _filter('evaluates to True')
        ['-r']
        >>> _filter(None)
        []
        >>> _filter(False)
        []
    """
    return ['-r'] if arg else []


def _fuzzy(arg=None):
    """
    Supported by some patches.

    Args:
        arg (bool): dmenu uses fuzzy matching. It matches items that have all
            characters entered, in sequence they are entered, but there may be
            any number of characters between matched characters. For example it
            takes "txt" makes it to "*t*x*t" glob pattern and checks if it
            matches.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _fuzzy()
        []
        >>> _fuzzy(True)
        ['-z']
        >>> _fuzzy('evaluates to True')
        ['-z']
        >>> _fuzzy(None)
        []
        >>> _fuzzy(False)
        []
    """
    return ['-z'] if arg else []


def _token(arg=None):
    """
    Supported by some patches.

    Args:
        arg (bool): dmenu uses space-separated tokens to match menu items.
            Using this overrides -z option.

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _token()
        []
        >>> _token(True)
        ['-t']
        >>> _token('evaluates to True')
        ['-t']
        >>> _token(None)
        []
        >>> _token(False)
        []
    """
    return ['-t'] if arg else []


def _mask(arg=None):
    """
    Supported by some patches.

    Args:
        arg (bool): dmenu masks input with asterisk characters (*).

    Returns:
        list: command line arguments to use with dmenu

    Examples:
        >>> _mask()
        []
        >>> _mask(True)
        ['-mask']
        >>> _mask('evaluates to True')
        ['-mask']
        >>> _mask(None)
        []
        >>> _mask(False)
        []
    """
    return ['-mask'] if arg else []


def _screen(arg=None):
    """
    Supported by some patches.

    Args:
        arg (int): dmenu appears on the specified screen number. Number given
            corresponds to screen number in X configuration.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _screen()
        []
        >>> _screen(1)
        ['-s', '1']
        >>> _screen('2')
        ['-s', '2']
        >>> _screen('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-s', str(int(arg))] if arg is not None else []


def _window_name(arg=None):
    """
    Supported by some patches.

    Args:
        arg (str): defines window name for dmenu. Defaults to "dmenu".

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _window_name()
        []
        >>> _window_name('some window name')
        ['-name', 'some window name']
        >>> _window_name('42')
        ['-name', '42']
    """
    return ['-name', str(arg)] if arg is not None else []


def _window_class(arg=None):
    """
    Supported by some patches.

    Args:
        arg (str): defines window class for dmenu. Defaults to "Dmenu".

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _window_class()
        []
        >>> _window_class('some window class')
        ['-class', 'some window class']
        >>> _window_class('42')
        ['-class', '42']
    """
    return ['-class', str(arg)] if arg is not None else []


def _opacity(arg=None):
    """
    Supported by some patches.

    Args:
        arg (float): defines window opacity for dmenu. Defaults to 1.0.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``float(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _opacity()
        []
        >>> _opacity(1)
        ['-o', '1.0']
        >>> _opacity('0.2')
        ['-o', '0.2']
        >>> _opacity(0.3)
        ['-o', '0.3']
    """
    return ['-o', str(float(arg))] if arg is not None else []


def _dim(arg=None):
    """
    Supported by some patches.

    Args:
        arg (float): enables screen dimming when dmenu appears. Takes dim
            opacity as argument.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``float(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _dim()
        []
        >>> _dim(1)
        ['-dim', '1.0']
        >>> _dim('0.2')
        ['-dim', '0.2']
        >>> _dim(0.3)
        ['-dim', '0.3']
    """
    return ['-dim', str(float(arg))] if arg is not None else []


def _dim_color(arg=None):
    """
    Supported by some patches.

    Args:
        arg (float): defines color of screen dimming. Active only when -dim in
            effect. Defaults to black (#000000)

    Returns:
        list: command line arguments to use with dmenu

    See Also:
        https://en.wikipedia.org/wiki/X11_color_names

    Raises:
        ValueError: Same as ``str(arg)`` if ``arg`` can't be casted.

    Examples:
        >>> _dim_color()
        []
        >>> _dim_color('#008')
        ['-dc', '#008']
        >>> _dim_color('#00008B')
        ['-dc', '#00008B']
        >>> _dim_color('Dark Blue')
        ['-dc', 'Dark Blue']
    """
    return ['-dc', str(arg)] if arg is not None else []


def _height(arg=None):
    """
    Supported by some patches.

    Args:
        arg (int): defines the height of the bar in pixels.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _height()
        []
        >>> _height(1)
        ['-h', '1']
        >>> _height('2')
        ['-h', '2']
        >>> _height('not castable') #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-h', str(int(arg))] if arg is not None else []


def _xoffset(arg=None):
    """
    Supported by some patches.

    Args:
        arg (int): defines the offset from the left border of the screen.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _xoffset()
        []
        >>> _xoffset(1)
        ['-x', '1']
        >>> _xoffset('2')
        ['-x', '2']
        >>> _xoffset('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-x', str(int(arg))] if arg is not None else []


def _yoffset(arg=None):
    """
    Supported by some patches.

    Args:
        arg (int): defines the offset from the top border of the screen.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _yoffset()
        []
        >>> _yoffset(1)
        ['-y', '1']
        >>> _yoffset('2')
        ['-y', '2']
        >>> _yoffset('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-y', str(int(arg))] if arg is not None else []


def _width(arg=None):
    """
    Supported by some patches.

    Args:
        arg (int): defines the desired menu window width.

    Returns:
        list: command line arguments to use with dmenu

    Raises:
        ValueError: Same as ``int(arg)``

    Examples:
        >>> _width()
        []
        >>> _width(1)
        ['-w', '1']
        >>> _width('2')
        ['-w', '2']
        >>> _width('not castable')
        Traceback (most recent call last):
        ...
        ValueError: invalid literal for int() with base 10: 'not castable'
    """
    return ['-w', str(int(arg))] if arg is not None else []


if __name__ == '__main__':
    import doctest
    flags = doctest.IGNORE_EXCEPTION_DETAIL | doctest.ELLIPSIS
    doctest.testmod(optionflags=flags)
