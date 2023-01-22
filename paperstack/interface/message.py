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

        Paramaters
        ----------
        message : str
        """

        print(message)


    def send_error(self, message):
        """Send error message in accordance with the medium. Print by
        default. Make sure to interrupt somehow, either by quitting program
        or raising exception.

        Paramaters
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

        Paramaters
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

        Paramaters
        ----------
        message : str
        """

        if self.ansi_colors:
            print(f'\033[32mSuccess:\033[0m {message}')
        else:
            print(f'Success: {message}')
