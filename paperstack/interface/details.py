"Module reponsible for the details panel."

import re

import urwid as u
import pyperclip

from paperstack.interface.keymap import Keymap
from paperstack.interface.util import clean_text
from paperstack.interface.message import AppMessengerError


class EntryElement(u.WidgetWrap):
    """The widget corresponding to each entry in details.

    Parameters
    ----------
    field_name : str
    name : str
    value : any
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__ (self, field_name, name, value, keymap):
        self.content = (field_name, name)

        self.keymap = keymap

        self.inherent_text = EntryElement.get_entry_text(
            field_name, name, value
        )
        self.text = u.Text(self.inherent_text)

        self.text_wrapper = u.AttrWrap(
            self.text,
            'entry'
        )

        super().__init__(u.Padding(self.text_wrapper, 'center', ('relative', 90)))


    @staticmethod
    def get_entry_text(field_name, name, value):
        """Get the text for an entry element.

        Parameters
        ----------
        field_name : str
        name : str
        value : str

        Returns
        -------
        str
        """

        text = [
            ('entry_name', f'{name}: ')
        ]

        if not value:
            text.append(('entry_empty', '(Blank)'))
        elif field_name == 'tags':
            tags = re.findall(
                r';(.*?);',
                clean_text(value)
            )

            for tag in tags:
                text.append(('tag', f' {tag} '))
                text.append(' ')
        else:
            text.append(clean_text(value))

        return text


    def keypress(self, size, key):
        "Handle keypresses."

        self.keymap.trigger(key)


    def selectable(self):
        return True


class EntrySeparator(u.WidgetWrap):
    "The widget corresponding to entry separators in details."

    def __init__ (self):
        self.content = ''

        super().__init__(u.Text(''))


    def keypress(self, size, key):
        "Handle keypresses."

        return key


    def selectable(self):
        return False


class DetailView(u.WidgetWrap):
    """Right panel, responsible for displaying details the selected record.

    Parameters
    ----------
    messenger : paperstack.interface.message.AppMessenger
    library : paperstack.data.library.Library
    global_keymap : paperstack.interface.keymap.Keymap
    vim_keys : bool

    Attributes
    ----------
    messenger : paperstack.interface.message.AppMessenger
    library : paperstack.data.library.Library
    keymap : paperstack.interface.keymap.Keymap
    has_focus : bool
    record : paperstack.data.record.Record
    previous_widget : urwid.Widget
        Keep track of last widget with focus.
    """

    def __init__(self, messenger, library, global_keymap, vim_keys):
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(messenger, global_keymap)

        self.has_focus = False

        self.previous_widget = None

        self.record = None

        if vim_keys:
            self.keymap.bind('h', 'Focus list', self.focus_list)
            self.keymap.bind('j', 'Next', self.focus_next)
            self.keymap.bind('k', 'Previous', self.focus_previous)
        else:
            self.keymap.bind('left', 'Focus list', self.focus_list)
            self.keymap.bind('down', 'Next', self.focus_next)
            self.keymap.bind('up', 'Previous', self.focus_previous)

        self.keymap.bind('e', 'Edit entry', self.edit_entry)
        self.keymap.bind(
            'E', 'Edit entry in editor', lambda: self.edit_entry(True)
        )
        self.keymap.bind('c', 'Copy entry', self.copy_entry)

        self.keymap.bind('g', 'First', self.focus_first)
        self.keymap.bind('G', 'Last', self.focus_last)

        self.keymap.bind('f', 'Find entry', self.focus_find)

        u.register_signal(self.__class__, ['focus_list'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        if self.has_focus:
            if self.previous_widget is not None:
                self.previous_widget.text.set_text(
                    self.previous_widget.inherent_text
                )

            widget, _ = self.walker.get_focus()

            if isinstance(widget, EntryElement):
                widget.text.set_text(
                        [('entry_selected', '― ')] + widget.inherent_text
                )

                self.previous_widget = widget

            self.keymap.show_hints()


    def focus_list(self):
        "Move focus to list panel."

        if self.previous_widget is not None:
            self.previous_widget.text.set_text(
                self.previous_widget.inherent_text
            )

        u.emit_signal(self, 'focus_list')


    def focus_previous(self):
        "Move focus to previous entry."

        try:
            while True:
                previous_index = self.walker.prev_position(
                    self.walker.get_focus()[1]
                )

                self.walker.set_focus(previous_index)

                if self.walker.get_focus()[0].selectable():
                    break
        except IndexError:
            pass


    def focus_next(self):
        "Move focus to next entry."

        try:
            while True:
                next_index = self.walker.next_position(
                    self.walker.get_focus()[1]
                )

                self.walker.set_focus(next_index)

                if self.walker.get_focus()[0].selectable():
                    break
        except IndexError:
            pass


    def focus_first(self):
        "Move focus to first entry."

        try:
            self.walker.set_focus(0)
        except IndexError:
            pass


    def focus_last(self):
        "Move focus to last entry."

        try:
            self.walker.set_focus(len(self.walker) - 1)
        except IndexError:
            pass


    def focus_find(self):
        "Move focus to first entry with matching entry name."

        def find(name):
            name = name.strip().lower()

            for i, widget in enumerate(self.walker):
                if not isinstance(widget, EntryElement):
                    continue

                entry_name, *_ = widget.text.get_text()[0].split(':')
                entry_name = entry_name.strip().lower()

                if entry_name.startswith(name):
                    self.walker.set_focus(i)
                    break

        self.messenger.ask_input('Entry name: ', '', find)



    def set_record(self, record):
        """Set the current record being viewed.

        Parameters
        ----------
        record : paperstack.data.record.Record
        """

        self.record = record

        if record is None:
            while len(self.walker) > 0:
                self.walker.pop()
            return

        widgets = []

        first_entry = True

        for key, name, *_ in record.requirements:
            if key in record.record and record.record[key]:
                value = record.record[key]
            else:
                value = ''

            if not first_entry:
                widgets.append(EntrySeparator())

            first_entry = False

            widgets.append(EntryElement(
                key,
                name,
                value,
                self.keymap
            ))

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)


    def edit_entry(self, editor_default=False):
        "Edit currently selected entry."

        widget, index = self.walker.get_focus()

        field_name, name = widget.content

        def commit_edit(text):
            old_entry = self.record.record[field_name]

            self.record[field_name] = text

            try:
                self.record.sanitize()
                self.record.validate()

                text = self.record.record[field_name] or ''

                record_id = self.record.record['record_id']

                self.library.update(record_id, {
                    field_name: text
                })
                self.library.commit()

                text = EntryElement.get_entry_text(field_name, name, text)
                widget.inherent_text = text

                widget.text.set_text(
                    [('entry_selected', '* ')] + text
                )

                self.messenger.send_success('Edited entry.')
            except AppMessengerError:
                self.record[field_name] = old_entry

        if field_name in self.record.record and self.record.record[field_name]:
            if field_name == 'tags':
                value = ', '.join(re.findall(
                    r';(.*?);',
                    self.record.record[field_name]
                ))
            else:
                value = self.record.record[field_name]
        else:
            value = ''

        self.messenger.ask_input(
            f'{name}: ',
            value,
            commit_edit,
            editor_default = editor_default
        )


    def copy_entry(self):
        "Copy currently selected entry."

        widget, _ = self.walker.get_focus()

        pyperclip.copy(
            self.record.record[widget.content[0]]
        )

        self.messenger.send_success('Copied entry to clipboard.')
