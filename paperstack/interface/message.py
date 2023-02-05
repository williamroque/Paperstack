"Module responsible for handling messages to the user."

import sys

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
    """

    def __init__(self, ansi_colors=True):
        self.app = None
        self.ansi_colors = ansi_colors


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
                    str(message)
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(str(message)),
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
                    f'Error: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f'Error: {message}'),
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
                self.app.change_colors('footer', 'dark yellow', '')


            if self.app.text_mode:
                self.app.footer_container.original_widget.set_text(
                    f'Warning: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f'Warning: {message}'),
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
                    f'Success: {message}'
                )
            else:
                self.app.footer_container.original_widget = u.AttrWrap(
                    u.Text(f'Success: {message}'),
                    'footer'
                )
                self.app.text_mode = True


    def ask_input(self, prompt, callback, *callback_args):
        """Ask for input using footer with `prompt`, then call `callback`
        with results.

        Parameters
        ----------
        prompt : str
        callback : func
        callback_args : list
        """

        if self.app is None:
            raise AppMessengerError

        editor = u.Edit(prompt)

        def escape(_):
            self.app.focus_list()
            self.app.list_view.keymap.show_hints()

            u.disconnect_signal(self.app, 'escape', escape)

        u.connect_signal(self.app, 'escape', escape)

        def enter(_):
            text = editor.get_edit_text()

            self.app.focus_list()
            self.app.list_view.keymap.show_hints()

            u.disconnect_signal(self.app, 'enter', enter)

            callback(text, *callback_args)

        u.connect_signal(self.app, 'enter', enter)

        self.app.footer_container.original_widget = editor
        self.app.text_mode = False
        self.app.focus_footer()
