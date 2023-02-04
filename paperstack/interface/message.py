"Module responsible for handling messages to the user."

import sys


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
            self.app.footer_text.set_text(message)


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

            self.app.footer_text.set_text(f'Error: {message}')

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

            self.app.footer_text.set_text(f'Warning: {message}')


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

            self.app.footer_text.set_text(f'Success: {message}')
