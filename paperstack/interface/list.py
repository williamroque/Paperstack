"Module responsible for the list panel."

from pathlib import Path
import os

import urwid as u

from paperstack.interface.keymap import Keymap
from paperstack.interface.util import clean_text
from paperstack.utility import open_path
from paperstack.filesystem.file import File


class RecordElement(u.WidgetWrap):
    """The Widget corresponding to each record item.

    Parameters
    ----------
    record : paperstack.data.record.Record
    width : int
        Panel width.
    keymap : paperstack.interface.keymap.Keymap

    Attributes
    ----------
    record : paperstack.data.record.Record
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__ (self, record, width, keymap):
        self.content = record

        title = clean_text(record.record['title'])

        self.text = u.Text(title, wrap='ellipsis')
        self.text_wrapper = u.AttrWrap(
            self.text,
            'record',
            'record_selected'
        )

        self.keymap = keymap

        super().__init__(u.Padding(self.text_wrapper, 'center', width - 1))


    def keypress(self, size, key):
        "Handle keypresses."

        self.keymap.trigger(key)


    def selectable(self):
        return True


class ListView(u.WidgetWrap):
    """This is the left panel, responsible for displaying the list of
    records.

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
    walker : urwid.SimpleFocusListWalker
        Walkers help reflect data onto UI elements.
    has_focus : bool
    previous_widget : urwid.Widget
        Keep track of last widget with focus.
    marks : set
        Currently selected records (actions on multiple records at a time).
    """

    def __init__(self, width, messenger, library, global_keymap, vim_keys):
        self.width = width
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(messenger, global_keymap)

        self.has_focus = False
        self.previous_widget = None

        self.marks = set()

        self.keymap.bind_combo(
            ['d', 'y'],
            ['Delete record', 'Confirm'],
            self.remove_record
        )
        self.keymap.bind('o', 'Open PDF', self.open_pdf)
        self.keymap.bind('m', 'Toggle mark', self.mark)
        self.keymap.bind('a', 'Mark all', self.mark_all)
        self.keymap.bind_combo(
            ['e', 'b'],
            ['Export', 'BibTeX'],
            self.export_bibtex
        )

        if vim_keys:
            self.keymap.bind('l', 'Focus details', self.focus_details)
            self.keymap.bind('j', 'Next', self.focus_next)
            self.keymap.bind('k', 'Previous', self.focus_previous)
        else:
            self.keymap.bind('right', 'Focus details', self.focus_details)
            self.keymap.bind('down', 'Next', self.focus_next)
            self.keymap.bind('up', 'Previous', self.focus_previous)

        u.register_signal(self.__class__, ['show_details', 'focus_details'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        if len(self.walker) == 0:
            u.emit_signal(self, 'show_details', None)
            return

        if self.has_focus:
            if self.previous_widget is not None:
                self.previous_widget.set_text(
                    self.previous_widget.get_text()[0][2:]
                )

            widget, _ = self.walker.get_focus()

            self.keymap.show_hints()

            widget.text.set_text(
                '→ ' + widget.text.get_text()[0]
            )

            self.previous_widget = widget.text

            u.emit_signal(self, 'show_details', widget.content)


    def focus_details(self):
        "Move focus to details panel."

        u.emit_signal(self, 'focus_details')


    def focus_previous(self, exclude=None):
        """Move focus to previous record.

        Parameters
        ----------
        exclude : set
            Exclude set of widgets, which may be deleted.
        """

        try:
            widget, index = self.walker.get_focus()

            self.walker.set_focus(
                self.walker.prev_position(index)
            )

            while exclude and widget in exclude:
                widget, index = self.walker.get_focus()

                self.walker.set_focus(
                    self.walker.prev_position(index)
                )

        except IndexError:
            pass


    def focus_next(self):
        "Move focus to next record."

        try:
            self.walker.set_focus(
                self.walker.next_position(self.walker.get_focus()[1])
            )
        except IndexError:
            pass


    def get_marks(self):
        """Get marked and currently selected widgets.

        Returns
        -------
        set
        """

        widget, _ = self.walker.get_focus()

        return {widget} | self.marks


    def remove_record(self):
        "Remove record from database."

        marks = self.get_marks()

        self.focus_previous(marks)

        for widget in marks:
            record = widget.content.record

            record_id = record['record_id']

            if 'path' in record and record['path']:
                os.remove(record['path'])

            self.library.remove(record_id)
            self.library.commit()

            index = self.walker.index(widget)

            del self.walker[index]

            if widget in self.marks:
                self.marks.remove(widget)

            self.messenger.send_success('Removed item(s).')


    def open_pdf(self):
        "Open PDF corresponding to record from database."

        marks = self.get_marks()

        for widget in marks:
            record = widget.content.record

            if 'path' in record and record['path']:
                path = Path(record['path'])

                if path.is_file():
                    try:
                        open_path(str(path.absolute()))
                    except Exception:
                        self.messenger.send_warning('Could not open PDF in preferred application.')
                else:
                    self.messenger.send_warning('Specified path does not exist.')
            else:
                self.messenger.send_warning('No PDF path specified.')


    def mark(self):
        "Toggle mark for current record (used by other actions later)."

        widget, index = self.walker.get_focus()

        if widget in self.marks:
            self.marks.remove(widget)
            widget.text_wrapper.set_attr('record')
        else:
            self.marks.add(widget)
            widget.text_wrapper.set_attr('entry_name')

        self.focus_next()


    def mark_all(self):
        "Toggle marks for all records."

        for widget in self.walker:
            if widget in self.marks:
                self.marks.remove(widget)
                widget.text_wrapper.set_attr('record')
            else:
                self.marks.add(widget)
                widget.text_wrapper.set_attr('entry_name')



    def export_bibtex(self):
        "Export current record to BibTeX and write to specified path."

        marks = self.get_marks()

        def write_bibtex(path):
            bibtex_file = File(path)
            bibtex_file.ensure()

            with open(bibtex_file.path, 'w') as f:
                for widget in marks:
                    text = widget.content.to_bibtex()
                    f.write(text)

            self.messenger.send_success('Exported BibTeX file.')

        self.messenger.ask_input(
            'Export path: ',
            'refs.bib',
            write_bibtex
        )


    def set_data(self, records):
        """Render list items for each record.

        Parameters
        ----------
        records : list
        """

        widgets = [RecordElement(
            record,
            self.width,
            self.keymap
        ) for record in records]

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)
