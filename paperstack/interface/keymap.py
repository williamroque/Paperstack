"A module for providing keymaps to the application interface."

from copy import deepcopy


class Keymap:
    """Keymap class for Urwid.

    Parameters
    ----------
    messenger : paperstack.interface.message.AppMessenger
    inherit : paperstack.interface.keymap.Keymap

    Attributes
    ----------
    messenger : paperstack.interface.message.AppMessenger
    """

    def __init__(self, messenger, inherit=None):
        self.messenger = messenger

        if inherit:
            self.keymap = deepcopy(inherit.keymap)
        else:
            self.keymap = {}


    def bind(self, key, hint, callback):
        """Create key binding.

        Parameters
        ----------
        key : str
        hint : str
            Short description of binding.
        callback : func
        """

        self.keymap[key] = (hint, callback)


    def trigger(self, key):
        """Call callback corresponding to key, if binding exists.

        Parameters
        ----------
        key : str

        Returns
        -------
        bool
            Whether key was in keymap.
        """

        if key in self.keymap:
            self.keymap[key][1]()


    def show_hints(self):
        "Show keymap hints."

        self.messenger.send_neutral(
            ' │ '.join(f'{key}: {hint}' for key, (hint, _) in self.keymap.items())
        )
