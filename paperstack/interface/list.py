"Module responsible for the list panel."

from pathlib import Path
import os

import urwid as u

import pyperclip

from paperstack.interface.keymap import Keymap
from paperstack.interface.util import clean_text
from paperstack.data.scrapers import scraper_constructors

from paperstack.interface.message import AppMessengerError

from paperstack.utility import open_path
from paperstack.filesystem.file import File


class RecordElement(u.WidgetWrap):
    """The Widget corresponding to each record item.

    Parameters
    ----------
    record : paperstack.data.record.Record
    keymap : paperstack.interface.keymap.Keymap

    Attributes
    ----------
    record : paperstack.data.record.Record
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__ (self, record, keymap):
        self.content = record

        title = clean_text(record.record['title'])

        self.text = u.Text(title, wrap='ellipsis')
        self.text_wrapper = u.AttrWrap(
            self.text,
            'record',
            'record_selected'
        )

        self.keymap = keymap

        super().__init__(u.Padding(self.text_wrapper, 'center', ('relative', 90)))


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
    config : paperstack.filesystem.config.Config
    messenger : paperstack.interface.message.AppMessenger
    library : paperstack.data.library.Library
    global_keymap : paperstack.interface.keymap.Keymap
    vim_keys : bool

    Attributes
    ----------
    config : paperstack.filesystem.config.Config
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

    def __init__(self, config, messenger, library, global_keymap, vim_keys):
        self.config = config
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(messenger, global_keymap)

        self.has_focus = False
        self.previous_widget = None

        self.marks = set()

        if vim_keys:
            self.keymap.bind('l', 'Focus details', self.focus_details)
            self.keymap.bind('j', 'Next', self.focus_next)
            self.keymap.bind('k', 'Previous', self.focus_previous)
        else:
            self.keymap.bind('right', 'Focus details', self.focus_details)
            self.keymap.bind('down', 'Next', self.focus_next)
            self.keymap.bind('up', 'Previous', self.focus_previous)

        self.keymap.bind_combo(
            ['d', 'y'],
            ['Delete record', 'Confirm'],
            self.remove_record
        )
        self.keymap.bind('o', 'Open PDF', self.open_pdf)
        self.keymap.bind_combo(
            ['e', 'b'],
            ['Export', 'BibTeX'],
            self.export_bibtex
        )
        self.keymap.bind_combo(
            ['e', 'c'],
            ['Export', 'Citation'],
            self.export_citation
        )
        self.keymap.bind_combo(
            ['p', 'a'],
            ['Populate record', 'ADS'],
            lambda: self.populate('ads')
        )
        self.keymap.bind_combo(
            ['p', 'x'],
            ['Populate record', 'arXiv'],
            lambda: self.populate('arxiv')
        )
        self.keymap.bind_combo(
            ['p', 'm'],
            ['Populate record', 'MNRAS'],
            lambda: self.populate('mnras')
        )
        self.keymap.bind('m', 'Toggle mark', self.mark)
        self.keymap.bind('M', 'Mark all', self.mark_all)

        u.register_signal(self.__class__, [
            'show_details',
            'focus_details',
            'update_data'
        ])

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
                try:
                    path = File(
                        self.config.get('paths', 'data'), True
                    ).join(record['path'])

                    os.remove(path)
                except FileNotFoundError:
                    pass

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
                path = File(
                    self.config.get('paths', 'data'), True
                ).join(record['path'])

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
            widget.text_wrapper.set_attr('record_marked')

        self.focus_next()


    def mark_all(self):
        "Toggle marks for all records."

        for widget in self.walker:
            if widget in self.marks:
                self.marks.remove(widget)
                widget.text_wrapper.set_attr('record')
            else:
                self.marks.add(widget)
                widget.text_wrapper.set_attr('record_marked')


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


    def export_citation(self):
        "Export current record to citation and write to specified path."

        marks = self.get_marks()

        def copy_citation(citation_type):
            citation_type = citation_type.strip()

            if not citation_type or citation_type == 'harvard':
                citation_type = 'harvard1'
            else:
                citation_types = list(marks)[0].content.get_csl()

                if citation_type in citation_types:
                    citation_type = citation_types[citation_type]
                else:
                    try:
                        self.messenger.send_error(
                            f'Citation style "{citation_type}" not available.'
                        )
                    except AppMessengerError:
                        pass

                    return

            text = []

            for widget in marks:
                text.append(
                    widget.content.to_citation(citation_type)
                )

            pyperclip.copy('\n'.join(text))

            self.messenger.send_success('Copied citation to clipboard.')

        self.messenger.ask_input(
            'Citation type: ',
            '',
            copy_citation
        )


    def populate(self, database):
        """Populate record with new data using `database`.

        database : str
        """

        try:
            if database not in scraper_constructors:
                self.messenger.send_error(f'Database `{database}` not supported.')

            constructor = scraper_constructors[database]

            for widget in self.get_marks():
                def scrape(replace_pdf, widget):
                    widget_record = widget.content.record

                    try:
                        scraper = constructor(
                            widget_record,
                            self.config,
                            self.messenger
                        )

                        record = scraper.create_record()

                        update_entries = {}

                        for key, value in record.record.items():
                            key_redundant = key in widget_record and widget_record[key]
                            key_redundant = key_redundant and not (
                                key == 'journal' and widget_record['journal'] == 'arXiv e-prints'
                            )

                            if value and not key_redundant:
                                update_entries[key] = value

                        if replace_pdf == 'y':
                            record.download_pdf(scraper)
                            update_entries['path'] = record.record['path']

                        self.library.update(
                            widget_record['record_id'],
                            update_entries
                        )
                        self.library.commit()

                        widget.content.record = {**widget_record, **update_entries}
                        u.emit_signal(self, 'show_details', widget.content)

                        self.messenger.send_success('Populated record.')
                    except AppMessengerError:
                        pass

                widget_record = widget.content.record

                if 'path' in widget_record and widget_record['path']:
                    self.messenger.ask_input(
                        'Replace PDF with newer version if available? (y/...) ',
                        '',
                        scrape,
                        widget
                    )
                else:
                    scrape('y', widget)

        except AppMessengerError:
            pass


    def set_data(self, records):
        """Render list items for each record.

        Parameters
        ----------
        records : list
        """

        widgets = [RecordElement(
            record,
            self.keymap
        ) for record in records]

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)
