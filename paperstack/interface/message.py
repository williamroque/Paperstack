"Module responsible for handling messages to the user."

import sys
import tempfile
import os

from subprocess import call

import urwid as u


class Messenger:
    """Proudly deliver messages to the user in a timely manner. Children of
    this messenger will surpass it in talent and style.

    Parameters
    ----------
    ansi_colors : bool
        If true, print with special colors using ANSI escape sequences.

    Attributes
    ----------
    ansi_colors : bool
        If true, print with special colors using ANSI escape sequences.
    """

    def __init__(self, ansi_colors=True):
        self.ansi_colors = ansi_colors


    def send_neutral(self, message):
        """Send neutral message in accordance with the medium. Print by
        default.

        Parameters
        ----------
        message : str
        """

        print(message)


    def send_error(self, message):
        """Send error message in accordance with the medium. Print by
        default. Make sure to interrupt somehow, either by quitting program
        or raising exception.

        Parameters
        ----------
        message : str
        """

        if self.ansi_colors:
            print(f'\033[31mError:\033[0m {message}')
        else:
            print(f'Error: {message}')

        sys.exit(1)


    def send_warning(self, message):
        """Send warning message in accordance with the medium. Print by
        default. Quit.

        Parameters
        ----------
        message : str
        """

        if self.ansi_colors:
            print(f'\033[33mWarning:\033[0m {message}')
        else:
            print(f'Warning: {message}')


    def send_success(self, message):
        """Send success message in accordance with the medium. Print by
        default.

        Parameters
        ----------
        message : str
        """

        if self.ansi_colors:
            print(f'\033[32mSuccess:\033[0m {message}')
        else:
            print(f'Success: {message}')


class AppMessengerError(Exception):
    "Exception raised whenever an error is sent using AppMessenger."


class AppMessenger:
    """Messenger for an App instance. Puts messages in the footer.

    Parameters
    ----------
    ansi_colors : bool
        If true, print with special colors using ANSI escape sequences.

    Attributes
    ----------
    app : paperstack.interface.app.App
    ansi_colors : bool
        If true, print with special colors using ANSI escape sequences.
    editor_command : str
        The command to use for editing long text.
    editor_extension : str
        The file extension to use for editing long text.
    input_active : list
        Whether currently accepting input.
    input_buffer : list
        Keep track of ask_input requests.
    """

    def __init__(self, ansi_colors=True):
        self.app = None

        self.ansi_colors = ansi_colors
        self.editor_command = 'vi'
        self.editor_extension = 'md'

        self.input_active = False
        self.input_buffer = []


    def connect_app(self, app):
        """Define the `App` instance the messenger will use.

        Parameters
        ----------
        app : paperstack.interface.app.App
        """

        self.app = app


    def send_neutral(self, message):
        """Send neutral message in accordance with the medium. Print by
        default.

        Parameters
        ----------
        message : str
        """

        if self.app is not None:
            self.app.change_colors('footer', '', '')

            if self.app.text_mode:
                self.app.footer_container.original_widget.set_text(
                    ' ' + str(message)
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(' ' + str(message)),
                    'footer'
                )
                self.app.text_mode = True


    def send_error(self, message):
        """Send error message in accordance with the medium. Print by
        default. Make sure to interrupt somehow, either by quitting program
        or raising exception.

        Parameters
        ----------
        message : str
        """

        if self.app is None:
            print(f'Error: {message}')
        else:
            if self.ansi_colors:
                self.app.change_colors('footer', 'dark red', '')


            if self.app.text_mode:
                self.app.footer_container.original_widget.set_text(
                    f' Error: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f' Error: {message}'),
                    'footer'
                )
                self.app.text_mode = True

        raise AppMessengerError


    def send_warning(self, message):
        """Send warning message in accordance with the medium. Print by
        default. Quit.

        Parameters
        ----------
        message : str
        """

        if self.app is None:
            print(f'Warning: {message}')
        else:
            if self.ansi_colors:
                self.app.change_colors('footer', 'yellow', '')


            if self.app.text_mode:
                self.app.footer_container.original_widget.set_text(
                    f' Warning: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f' Warning: {message}'),
                    'footer'
                )
                self.app.text_mode = True


    def send_success(self, message):
        """Send success message in accordance with the medium. Print by
        default.

        Parameters
        ----------
        message : str
        """

        if self.app is None:
            print(f'Success: {message}')
        else:
            if self.ansi_colors:
                self.app.change_colors('footer', 'dark green', '')


            if self.app.text_mode:
                self.app.footer_container.original_widget.set_text(
                    f' Success: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f' Success: {message}'),
                    'footer'
                )
                self.app.text_mode = True


    def open_external_editor(self, default=''):
        """Open external editor and get text.

        Parameters
        ----------
        default : str
            Default text to set in the editor.
        """

        fd, filename = tempfile.mkstemp(
            suffix=f'.{self.editor_extension}'
        )

        os.close(fd)

        with open(filename, 'w') as f:
            f.write(default)

        self.app.loop.screen.stop()

        try:
            if '@FILE' in self.editor_command:
                call(self.editor_command.replace('@FILE', f.name), shell=True)
            else:
                call([self.editor_command, f.name])

        except Exception:
            self.send_warning(f'Could not connect to editor using command `{self.editor_command}`.')

        self.app.loop.screen.start()

        with open(filename) as f:
            text = f.read().strip()

        os.remove(filename)

        return text


    def open_editor(self, prompt, default, callback, *callback_args):
        """ Ask for input using footer with `prompt` and with `default`
        value, then call `callback` with results.

        Parameters
        ----------
        prompt : str
        default : str
        callback : func
        callback_args : list
        """

        if self.app is None:
            raise AppMessengerError

        if self.app.list_view.has_focus:
            previous_focus = 'list'
        else:
            previous_focus = 'details'

        editor = u.Edit(prompt, default, wrap=u.CLIP)

        def escape(_):
            if previous_focus == 'list':
                self.app.focus_list()
                self.app.list_view.keymap.show_hints()
            else:
                self.app.focus_details()
                self.app.detail_view.keymap.show_hints()

            u.disconnect_signal(self.app, 'enter', enter)
            u.disconnect_signal(self.app, 'escape', escape)
            u.disconnect_signal(self.app, 'ctrl-e', switch_editor)

            self.input_active = False

            if len(self.input_buffer) > 0:
                self.ask_input(*self.input_buffer.pop(0))

        u.connect_signal(self.app, 'escape', escape)

        def enter(_):
            text = editor.get_edit_text()

            if previous_focus == 'list':
                self.app.focus_list()
                self.app.list_view.keymap.show_hints()
            else:
                self.app.focus_details()
                self.app.detail_view.keymap.show_hints()

            u.disconnect_signal(self.app, 'enter', enter)
            u.disconnect_signal(self.app, 'escape', escape)
            u.disconnect_signal(self.app, 'ctrl-e', switch_editor)

            callback(text, *callback_args)

            self.input_active = False

            if len(self.input_buffer) > 0:
                self.ask_input(*self.input_buffer.pop(0))

        u.connect_signal(self.app, 'enter', enter)

        def switch_editor(_):
            default_text = editor.get_edit_text()

            editor.set_edit_text(
                self.open_external_editor(default_text)
            )
            editor.set_edit_pos(
                len(editor.get_edit_text())
            )

        u.connect_signal(self.app, 'ctrl-e', switch_editor)

        self.app.footer_container.original_widget = editor
        self.app.text_mode = False
        self.app.focus_footer()


    def ask_input(self, prompt, default, callback, *callback_args, editor_default=False):
        """Ask for input using either internal or external editor.

        Parameters
        ----------
        prompt : str
        default : str
        callback : func
        callback_args : list
        editor_default : bool
            Whether switch to external editor directly.
        """

        if self.input_active:
            self.input_buffer.append(
                (prompt, default, callback, *callback_args)
            )
            return

        self.input_active = True

        if editor_default:
            callback(self.open_external_editor(default), *callback_args)

            self.input_active = False

            if len(self.input_buffer) > 0:
                self.ask_input(*self.input_buffer.pop(0))
        else:
            self.open_editor(prompt, default, callback, *callback_args)
