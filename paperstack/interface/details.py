"Module reponsible for the details panel."

import urwid as u

from paperstack.interface.keymap import Keymap
from paperstack.interface.util import clean_text


class EntryElement(u.WidgetWrap):
    """The widget corresponding to each entry in details.

    Parameters
    ----------
    field_name : str
    name : str
    value : any
    width : int
        Panel width.
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__ (self, field_name, name, value, width, keymap):
        self.content = (field_name, name)

        self.keymap = keymap

        text = clean_text(value)

        text = [
            ('entry_name', f'{name}: '), clean_text(value)
        ]

        self.text = u.Text(text)

        self.text_wrapper = u.AttrWrap(
            self.text,
            'entry',
            'entry_selected'
        )

        super().__init__(u.Padding(self.text_wrapper, 'center', width - 2))


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
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    library : paperstack.data.library.Library
    global_keymap : paperstack.interface.keymap.Keymap
    vim_keys : bool

    Attributes
    ----------
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    library : paperstack.data.library.Library
    keymap : paperstack.interface.keymap.Keymap
    has_focus : bool
    record : paperstack.data.record.Record
    """

    def __init__(self, width, messenger, library, global_keymap, vim_keys):
        self.width = width
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(messenger, global_keymap)

        self.has_focus = False

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

        u.register_signal(self.__class__, ['focus_list'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        if self.has_focus:
            widget, _ = self.walker.get_focus()

            self.keymap.show_hints()


    def focus_list(self):
        "Move focus to list panel."

        u.emit_signal(self, 'focus_list')


    def focus_previous(self):
        "Move focus to previous record."

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
        "Move focus to next record."

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
                self.width,
                self.keymap
            ))

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)


    def edit_entry(self):
        "Edit currently selected entry."

        widget, index = self.walker.get_focus()

        field_name, name = widget.content

        def commit_edit(text):
            self.record.record[field_name] = text

            record_id = self.record.record['record_id']

            self.library.update(record_id, {
                field_name: text
            })
            self.library.commit()

            widget.text.set_text([
                ('entry_name', f'{name}: '), clean_text(text)
            ])

        if field_name in self.record.record and self.record.record[field_name]:
            value = self.record.record[field_name]
        else:
            value = ''

        self.messenger.ask_input(
            f'{name}: ',
            value,
            commit_edit
        )
