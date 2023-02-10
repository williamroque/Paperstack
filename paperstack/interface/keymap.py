"A module for providing keymaps to the application interface."

from copy import copy

import urwid as u


class Keymap:
    """Keymap class for Urwid.

    Parameters
    ----------
    messenger : paperstack.interface.message.AppMessenger
    inherit : paperstack.interface.keymap.Keymap

    Attributes
    ----------
    messenger : paperstack.interface.message.AppMessenger
    combo_keys : list
    active_map : dict
        Currently active keymap in a key combo or otherwise.
    screen : urwid.raw_display.Screen
    """

    def __init__(self, messenger, inherit=None):
        self.messenger = messenger

        if inherit:
            self.keymap = copy(inherit.keymap)
        else:
            self.keymap = {}

        self.combo_keys = []
        self.active_map = self.keymap

        self.screen = u.raw_display.Screen()


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


    def bind_combo(self, keys, hints, callback):
        """Create key binding.

        Parameters
        ----------
        keys : list
            List of keys for a combo.
        hints : list
            Short descriptions of binding for each key in combo.
        callback : func

        """

        keymap = self.keymap

        for i, key in enumerate(keys[:-1]):
            if not key in keymap:
                keymap[key] = { 'hint': hints[i] }
            keymap = keymap[key]

        keymap[keys[-1]] = (hints[-1], callback)


    def trigger(self, key):
        """Call callback corresponding to key, if binding exists.

        Parameters
        ----------
        key : str
        """

        if key in self.active_map:
            binding = self.active_map[key]

            if isinstance(binding, dict):
                self.active_map = binding
                self.combo_keys.append(key)

                self.show_hints()
            else:
                self.active_map = self.keymap
                self.combo_keys = []
                binding[1]()
        else:
            self.active_map = self.keymap
            self.combo_keys = []

            self.show_hints()


    def show_hints(self):
        "Show keymap hints."

        hints = []

        for key, binding in self.active_map.items():
            if key == 'hint':
                continue

            if isinstance(binding, dict):
                hint = binding['hint']
            else:
                hint = binding[0]

            hints.append(f'{key}: {hint}')

        size = self.screen.get_cols_rows()
        width = size[0] - 2

        message = ''

        if len(self.combo_keys) > 0:
            message += ' '.join(self.combo_keys) + '- '

        max_hints = 0
        accumulated_length = len(message) + 4

        for hint in hints:
            accumulated_length += len(hint) + 3

            if accumulated_length > width:
                break

            max_hints += 1

        message += ' │ '.join(hints[:max_hints])

        if max_hints < len(hints):
            message += ' │ ...'

        self.messenger.send_neutral(message)
