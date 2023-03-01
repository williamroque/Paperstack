"This is where the 'graphical' interface magic happens."

from copy import copy
import re

import fitz

import os

import urwid as u

from paperstack.filesystem.file import File

from paperstack.interface.keymap import Keymap
from paperstack.interface.message import AppMessengerError
from paperstack.data.record import record_constructors
from paperstack.data.scrapers import scraper_constructors

from paperstack.interface.list import ListView
from paperstack.interface.details import DetailView

from paperstack.utility import parse_dict


class App:
    "The main app."

    def __init__(self, config, messenger, library):
        self.config = config
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(self.messenger)

        self.keymap.bind('q', 'Exit app', self.quit)

        self.keymap.bind_combo(
            ['a', 'm', 'a'],
            ['Add record', 'Manually', 'Article'],
            lambda: self.add_manual('article')
        )
        self.keymap.bind_combo(
            ['a', 's', 'a'],
            ['Add record', 'Scrape', 'ADS'],
            lambda: self.add_scraped('ads')
        )
        self.keymap.bind_combo(
            ['a', 's', 'x'],
            ['Add record', 'Scrape', 'arXiv'],
            lambda: self.add_scraped('arxiv')
        )
        self.keymap.bind_combo(
            ['a', 's', 'm'],
            ['Add record', 'Scrape', 'MNRAS'],
            lambda: self.add_scraped('mnras')
        )

        self.keymap.bind('f', 'Filter', self.filter_records)

        self.palette = {
            ('bg', '', ''),
            ('record', '', ''),
            ('record_selected', 'dark green', ''),
            ('record_marked', 'dark blue', ''),
            ('entry_selected', 'dark blue', ''),
            ('entry_name', 'dark blue', ''),
            ('entry_empty', 'dark gray, italics', ''),
            ('footer', '', ''),
            ('tag', 'black', 'light blue')
        }

        screen = u.raw_display.Screen()

        screen.tty_signal_keys(
            'undefined','undefined', 'undefined','undefined','undefined'
        )

        size = screen.get_cols_rows()
        width = size[0] - 2
        height = size[1] - 2

        list_ratio = 40
        detail_ratio = 100 - list_ratio

        width_threshold = 70

        if width < width_threshold:
            list_height = height * list_ratio // 100 - 2
            detail_height = height * detail_ratio // 100 - 2
        else:
            list_height = height
            detail_height = height

        vim_keys = self.config.get('keys', 'vim-bindings') == 'yes'

        self.list_view = ListView(
            self.config,
            self.messenger,
            self.library,
            self.keymap,
            vim_keys
        )
        self.detail_view = DetailView(
            self.messenger,
            self.library,
            self.keymap,
            vim_keys
        )

        u.connect_signal(self.list_view, 'show_details', self.show_details)
        u.connect_signal(self.list_view, 'focus_details', self.focus_details)
        u.connect_signal(self.list_view, 'update_data', self.update_data)

        u.connect_signal(self.detail_view, 'focus_list', self.focus_list)

        u.register_signal(self.__class__, ['escape', 'enter', 'ctrl-e'])

        self.text_mode = True

        footer_text = u.AttrWrap(u.Text(''), 'footer')

        self.footer_container = u.WidgetPlaceholder(footer_text)

        list_filler = u.Filler(
            self.list_view,
            valign = 'top',
            height = list_height
        )
        detail_filler = u.Filler(
            self.detail_view,
            valign = 'top',
            height = detail_height
        )

        list_panel = u.LineBox(
            list_filler,
            title = 'Records'
        )
        detail_panel = u.LineBox(
            detail_filler,
            title = 'Details'
        )

        if width < width_threshold:
            self.columns = u.Pile([
                ('weight', list_ratio, list_panel),
                ('weight', detail_ratio, detail_panel)
            ])
        else:
            self.columns = u.Columns([
                ('weight', list_ratio, list_panel),
                ('weight', detail_ratio, detail_panel)
            ])

        self.frame = u.Frame(
            body = self.columns,
            footer = self.footer_container
        )

        self.loop = u.MainLoop(
            u.AttrMap(self.frame, 'bg'),
            self.palette,
            unhandled_input = self.unhandled_input,
            handle_mouse = False
        )

        self.focus_list()


    def change_colors(self, entry, foreground, background):
        """Change palette colors for a specific entry.

        Parameters
        ----------
        entry : str
        foreground : str
        background : str

        Attributes
        ----------
        entry : str
        foreground : str
        background : str
        """

        self.loop.screen.register_palette_entry(
            entry,
            foreground,
            background
        )
        self.loop.screen.clear()


    def quit(self):
        "Quit app."

        raise u.ExitMainLoop()


    def filter_records(self):
        "Filter and display records."

        for widget in self.list_view.walker:
            if widget in self.list_view.marks:
                self.list_view.marks.remove(widget)
                widget.text_wrapper.set_attr('record')

        self.list_view.marks.clear()

        def display(text):
            filters = list(parse_dict(text, 'title').items())

            try:
                records = self.library.filter(filters)

                self.update_data(records)
            except AppMessengerError:
                pass

        self.messenger.ask_input(
            'Filter: ', '', display
        )


    def unhandled_input(self, key):
        """Take care of global key bindings.

        Parameters
        ----------
        key : str
        """

        if key == 'enter':
            u.emit_signal(self, 'enter', None)
        elif key in ('esc', 'ctrl g'):
            u.emit_signal(self, 'escape', None)
        elif key == 'ctrl e':
            u.emit_signal(self, 'ctrl-e', None)
        elif self.text_mode:
            self.keymap.trigger(key)


    def show_details(self, record):
        """Show record details in detail view.

        Parameters
        ----------
        record : paperstack.data.record.Record
        """

        self.detail_view.set_record(record)


    def focus_list(self):
        "Move focus to list panel."

        self.frame.set_focus('body')

        self.list_view.keymap.show_hints()
        self.list_view.has_focus = True
        self.detail_view.has_focus = False
        self.columns.set_focus(0)


    def focus_details(self):
        "Move focus to details panel."

        self.frame.set_focus('body')

        self.detail_view.keymap.show_hints()
        self.list_view.has_focus = False
        self.detail_view.has_focus = True
        self.detail_view.modified()
        self.columns.set_focus(1)


    def focus_footer(self):
        "Move focus to footer."

        self.list_view.has_focus = False
        self.detail_view.has_focus = True

        self.frame.set_focus('footer')


    def add_manual(self, record_type, **entries):
        "Add record type manually."

        try:
            if record_type not in record_constructors:
                self.messenger.send_error(f'Record type `{record_type}` does not exist.')

            constructor = record_constructors[record_type]
            record = constructor(entries, self.config, self.messenger, True)

            ignore_fields = ('record_id', 'path') + tuple(entries.keys())

            requirements = []

            for requirement in copy(record.requirements):
                if requirement[0] not in ignore_fields:
                    requirements.append(requirement)

            def callback(text, requirement):
                record[requirement[0]] = text

                if len(requirements) > 0:
                    requirement = requirements.pop(0)
                    self.messenger.ask_input(
                        f'{requirement[1]}: ',
                        '',
                        callback,
                        requirement
                    )
                else:
                    try:
                        record.setup()
                        record.validate()

                        self.library.add(record)
                        self.library.commit()

                        self.update_data(
                            self.library.filter([])
                        )

                        self.messenger.send_success('Added record.')
                    except AppMessengerError:
                        pass

            requirement = requirements.pop(0)
            self.messenger.ask_input(
                f'{requirement[1]}: ',
                '',
                callback,
                requirement
            )
        except AppMessengerError:
            pass


    def add_scraped(self, database, **entries):
        """Scrape database using information provided by input..

        Parameters
        ----------
        database : str
        entries : dict
            All entries that are pre-established.
        """

        try:
            if database not in scraper_constructors:
                self.messenger.send_error(f'Database `{database}` not supported.')

            constructor = scraper_constructors[database]
            scraper = constructor(entries, self.config, self.messenger)

            if len(entries) == 0:
                suggested_fields = copy(scraper.suggested_fields)
            else:
                suggested_fields = []

            def scrape():
                try:
                    record = scraper.create_record()

                    if 'path' not in entries:
                        record.download_pdf(scraper)

                    self.library.add(record)
                    self.library.commit()

                    self.update_data(
                        self.library.filter([])
                    )

                    self.messenger.send_success('Added record.')
                except AppMessengerError:
                    pass

            def callback(text, field):
                scraper.record[field[0]] = text

                if len(suggested_fields) > 0:
                    field = suggested_fields.pop(0)
                    self.messenger.ask_input(
                        f'{field[1]}: ',
                        '',
                        callback,
                        field
                    )
                else:
                    scrape()

            if len(suggested_fields) > 0:
                field = suggested_fields.pop(0)
                self.messenger.ask_input(
                    f'{field[1]}: ',
                    '',
                    callback,
                    field
                )
            else:
                scrape()
        except AppMessengerError:
            pass


    def update_data(self, records):
        """Render list items for each record.

        Parameters
        ----------
        records : list
        """

        self.list_view.set_data(records)


    def start(self):
        "Start app."

        records = self.library.filter([])

        self.update_data(records)

        record_paths = set(record.record['path'] for record in records)
        data_paths = os.listdir(File(
            self.config.get('paths', 'data'), True
        ).path)

        def handle_add(scrape, path):
            if scrape == 'y':
                absolute_path = File(
                    self.config.get('paths', 'data'), True
                ).join(path)

                doc = fitz.open(absolute_path)

                for page in doc:
                    text = page.get_text()

                    arxiv = re.search(
                        r'(?<=arxiv:)([0-9]+\.?[0-9]+)([vV0-9]*)',
                        text,
                        re.I
                    )

                    doi = re.search(
                        r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b',
                        text
                    )

                    if arxiv:
                        self.add_scraped(
                            'arxiv',
                            arxiv = arxiv.group(0),
                            path = path
                        )
                        break

                    if doi:
                        self.add_scraped(
                            'ads',
                            doi = doi.group(0),
                            path = path
                        )
                        break
            else:
                self.add_manual('article', path = path)

        def handle_file(option, path):
            if option == 'a':
                self.messenger.ask_input(
                    'Scrape? (y/...) ',
                    '',
                    handle_add,
                    path
                )
            elif option == 'd':
                try:
                    absolute_path = File(
                        self.config.get('paths', 'data'), True
                    ).join(path)

                    os.remove(absolute_path)

                    self.messenger.send_success('Deleted file.')
                except:
                    self.messenger.send_warning('Unable to delete file.')

        for path in data_paths:
            if path.endswith('.pdf') and path not in record_paths:
                self.messenger.ask_input(
                    'Unrecognized file `{}`. Add to library, delete, or ignore? (a/d/...) '.format(
                        path[:17] + '...' if len(path) > 20 else path
                    ),
                    '',
                    handle_file,
                    path
                )

        self.loop.run()
