"This is where the 'graphical' interface magic happens."

import urwid as u

from paperstack.interface.keymap import Keymap
from paperstack.interface.message import AppMessenger
from paperstack.filesystem.config import Config

from paperstack.interface.list import ListView
from paperstack.interface.details import DetailView


class App:
    "The main app."

    def __init__(self, config, messenger, library):
        self.config = config
        self.messenger = messenger
        self.library = library
        self.keymap = Keymap(self.messenger)

        self.keymap.bind('q', 'Exit app', self.quit)

        self.palette = {
            ('bg', '', ''),
            ('record', '', ''),
            ('record_selected', 'dark green', ''),
            ('record_marked', 'white', 'dark blue'),
            ('entry_selected', 'underline', ''),
            ('entry_marked', 'white', 'dark blue'),
            ('entry_name', 'dark blue', ''),
            ('footer', '', '')
        }

        size = u.raw_display.Screen().get_cols_rows()
        width = size[0] - 2
        height = size[1] - 2

        list_ratio = 40
        detail_ratio = 100 - list_ratio

        width_threshold = 70

        if width < width_threshold:
            list_width = width
            detail_width = width

            list_height = height * list_ratio // 100 - 2
            detail_height = height * detail_ratio // 100 - 2
        else:
            list_width = width * list_ratio // 100 - 2
            detail_width = width * detail_ratio // 100 - 2

            list_height = height
            detail_height = height

        vim_keys = self.config.get('keys', 'vim-bindings') == 'yes'

        self.list_view = ListView(
            list_width,
            self.messenger,
            self.library,
            self.keymap,
            vim_keys
        )
        self.detail_view = DetailView(
            detail_width,
            self.messenger,
            self.keymap,
            vim_keys
        )

        u.connect_signal(self.list_view, 'show_details', self.show_details)
        u.connect_signal(self.list_view, 'focus_details', self.focus_details)

        u.connect_signal(self.detail_view, 'focus_list', self.focus_list)

        self.footer_text = u.Text('')
        footer = u.AttrWrap(self.footer_text, 'footer')

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

        frame = u.AttrMap(u.Frame(
            body = self.columns,
            footer = footer
        ), 'bg')

        self.loop = u.MainLoop(
            frame,
            self.palette,
            unhandled_input = self.unhandled_input
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


    def unhandled_input(self, key):
        """Take care of global key bindings.

        Parameters
        ----------
        key : str
        """

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

        self.list_view.keymap.show_hints()
        self.list_view.has_focus = True
        self.detail_view.has_focus = False
        self.columns.set_focus(0)


    def focus_details(self):
        "Move focus to details panel."

        self.detail_view.keymap.show_hints()
        self.list_view.has_focus = False
        self.detail_view.has_focus = True
        self.columns.set_focus(1)


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
        self.loop.run()
