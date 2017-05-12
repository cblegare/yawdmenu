#!/usr/bin/python
# coding: utf-8


from collections import OrderedDict
import subprocess

import six

from xdmenu import DmenuError, DmenuUsageError

class Dmenu(object):
    def __init__(self, proc_runner=None, **kwargs):
        """
        An extensible dmenu wrapper.

        Args:
            proc_runner (Callable[[list, list], str]): a function that calls
               dmenu as a subprocess and returns the output.

            dmenu (str): dmenu executable to use.

            bottom (bool): dmenu appears at the bottom of the screen.

            grab (bool): dmenu grabs the keyboard before reading stdin.  This
                is faster, but will lock up X until stdin reaches end-of-file.

            insensitive (bool): dmenu matches menu items case insensitively.

            lines (int): dmenu lists items vertically, with the given number of
                lines.

            monitor (int): dmenu is displayed on the monitor number supplied.
                Monitor numbers are starting from 0.

            prompt (str): defines the prompt to be displayed to the left of the
                input field.

            font (str): defines the font or font set used.

            normal_bg_color (str): defines the normal background color.  #RGB,
                #RRGGBB, and X color names are supported.

            normal_fg_color (str): defines the normal foreground color.

            selected_bg_color (str): defines the selected background color.

            selected_fg_color (str): defines the selected foreground color.

            windowid (str): embed into windowid.

        """
        self._dmenu_args = OrderedDict()
        # With python >= 3.6, we could initialise this OrderedDict with
        # keyword arguments.  Since otherwise the order is lost, our nice
        # doctests below would fail.
        self._dmenu_args['dmenu'] = _dmenu
        self._dmenu_args['bottom'] = _bottom
        self._dmenu_args['grab'] = _grab
        self._dmenu_args['insensitive'] = _insensitive
        self._dmenu_args['lines'] = _lines
        self._dmenu_args['monitor'] = _monitor
        self._dmenu_args['prompt'] = _prompt
        self._dmenu_args['font'] = _font
        self._dmenu_args['normal_bg_color'] = _normal_bg_color
        self._dmenu_args['normal_fg_color'] = _normal_fg_color
        self._dmenu_args['selected_bg_color'] = _selected_bg_color
        self._dmenu_args['selected_fg_color'] = _selected_fg_color
        self._dmenu_args['windowid'] = _windowid
        # The following arguments are not standard options for dmenu
        # For example, dmenu2 has them all:
        # https://bitbucket.org/melek/dmenu2
        self._dmenu_args['filter'] = _filter
        self._dmenu_args['fuzzy'] = _fuzzy
        self._dmenu_args['token'] = _token
        self._dmenu_args['mask'] = _mask
        self._dmenu_args['screen'] = _screen
        self._dmenu_args['window_name'] = _window_name
        self._dmenu_args['window_class'] = _window_class
        self._dmenu_args['opacity'] = _opacity
        self._dmenu_args['dim'] = _dim
        self._dmenu_args['dim_color'] = _dim_color
        self._dmenu_args['height'] = _height
        self._dmenu_args['xoffset'] = _xoffset
        self._dmenu_args['yoffset'] = _yoffset
        self._dmenu_args['width'] = _width

        self._run_dmenu_process = proc_runner or _run_dmenu_process
        self._dmenu_config = OrderedDict()
        self._dmenu_config['dmenu'] = 'dmenu'
        for name in self._dmenu_args:
            self._dmenu_config[name] = None
        self._dmenu_config.update(kwargs)

    def make_cmd(self, **kwargs):
        """
        Build the list of command line arguments to dmenu.

        Args:
            \*\*kwargs: Any of the supported argument or added via
                :meth:`.add_arg`.

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
            \*\*kwargs: Any of the supported argument or added via
                :meth:`.add_arg`.

        Returns:
            str: What the user chose.

        Examples:

            >>> def mocked_process(cmd, input_lines=None):
            ...     # We mock the _run_dmenu_process function for this example
            ...     # to be runnable even if dmenu is not installed
            ...     #
            ...     # We assert to be called only with 'dmenu' for the purpose
            ...     # of this example.
            ...     assert cmd == ['dmenu']
            ...     # this one will always return the first line if possible
            ...     return input_lines[0] if input_lines else ''
            >>> m = Dmenu(proc_runner=mocked_process)
            >>> m.run(['foo', 'bar'])
            'foo'

        Returns:
            list: All the choices made by the user.
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
        self._dmenu_config[name] = default


def dmenu(choices, dmenu=None, **kwargs):
    """
    Run `dmenu` with configuration provided in ``**kwargs``.

    Args:
        choices (list): Choices to put in menu
        dmenu (Dmenu): A :class:`.Dmenu` instance to use.  If not provided, a
            default one will be created.
        \*\*kwargs: Any of the supported argument or added via
            :meth:`.Dmenu.add_arg`.

    Returns:
        list: All the choices made by the user.

    See Also:
        :meth:`xdmenu.Dmenu.run`
    """
    dmenu_instance = dmenu or Dmenu(**kwargs)
    return dmenu_instance.run(choices)


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
