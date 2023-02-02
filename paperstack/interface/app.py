"This is where the 'graphical' interface magic happens."

import re

import urwid as u

from paperstack.interface.keymap import Keymap
from paperstack.interface.message import AppMessenger
from paperstack.filesystem.config import Config


def clean_text(text):
    """Clean text from BibTeX entry.

    Parameters
    ----------
    text : str
    """

    accents = [
        ('`', 'a', 'à'),
        ('`', 'e', 'è'),
        ('`', 'i', 'ì'),
        ('`', 'o', 'ò'),
        ('`', 'u', 'ù'),

        ('\'', 'a', 'á'),
        ('\'', 'e', 'é'),
        ('\'', 'i', 'í'),
        ('\'', 'o', 'ó'),
        ('\'', 'u', 'ú'),

        ('"', 'a', 'ä'),
        ('"', 'e', 'ë'),
        ('"', 'i', 'ï'),
        ('"', 'o', 'ö'),
        ('"', 'u', 'ü'),

        ('\\^', 'a', 'â'),
        ('\\^', 'e', 'ê'),
        ('\\^', 'i', 'î'),
        ('\\^', 'o', 'ô'),
        ('\\^', 'u', 'û'),

        ('~', 'a', 'ã'),
        ('~', 'o', 'õ'),
        ('~', 'n', 'ñ'),

        ('c', 'c', 'ç'),
    ]

    template = r'\\{accent}{letter}|{{\\{accent}{letter}}}|\\{accent}{{{letter}}}'

    for accent, letter, sub in accents:
        text = re.sub(
            template.format(accent = accent, letter = letter),
            sub, text
        )
        text = re.sub(
            template.format(accent = accent, letter = letter.upper()),
            sub.upper(), text
        )

    text = re.sub(r'^{(.*)}$', '\\1', text)
    text = re.sub(r'{(.*?)}', '\\1', text)
    text = re.sub(r'\.~', '. ', text)

    return text


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

        self.text = u.AttrWrap(
            u.Text(title, wrap='ellipsis'),
            'record',
            'record_selected'
        )

        self.keymap = keymap

        super().__init__(u.Padding(self.text, 'center', width - 1))


    def keypress(self, size, key):
        "Handle keypresses."

        self.keymap.trigger(key)


    def selectable(self):
        return True


class EntryElement(u.WidgetWrap):
    """The widget corresponding to each entry in details.

    Parameters
    ----------
    name : paperstack.data.record.Record
    value : any
    width : int
        Panel width.
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__ (self, name, value, width, keymap):
        self.content = value

        self.keymap = keymap

        text = clean_text(value)

        text = [
            ('entry_name', f'{name}: '), clean_text(value)
        ]

        self.text = u.AttrWrap(
            u.Text(text),
            'entry',
            'entry_selected'
        )

        super().__init__(u.Padding(self.text, 'center', width - 2))


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


class ListView(u.WidgetWrap):
    """This is the left panel, responsible for displaying the list of
    records.

    Parameters
    ----------
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    global_keymap : paperstack.interface.keymap.Keymap
    vim_keys : bool

    Attributes
    ----------
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    keymap : paperstack.interface.keymap.Keymap
    walker : urwid.SimpleFocusListWalker
        Walkers help reflect data onto UI elements.
    """

    def __init__(self, width, messenger, global_keymap, vim_keys):
        self.width = width
        self.messenger = messenger
        self.keymap = Keymap(messenger, global_keymap)

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

        widget, _ = self.walker.get_focus()

        u.emit_signal(self, 'show_details', widget.content)


    def focus_details(self):
        "Move focus to details panel."

        u.emit_signal(self, 'focus_details')


    def focus_previous(self):
        "Move focus to previous record."

        try:
            self.walker.set_focus(
                self.walker.prev_position(self.walker.get_focus()[1])
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


class DetailView(u.WidgetWrap):
    """Right panel, responsible for displaying details the selected record.

    Parameters
    ----------
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    global_keymap : paperstack.interface.keymap.Keymap
    vim_keys : bool

    Attributes
    ----------
    width : int
        Panel width.
    messenger : paperstack.interface.message.AppMessenger
    keymap : paperstack.interface.keymap.Keymap
    """

    def __init__(self, width, messenger, global_keymap, vim_keys):
        self.width = width
        self.messenger = messenger
        self.keymap = Keymap(messenger, global_keymap)

        if vim_keys:
            self.keymap.bind('h', 'Focus list', self.focus_list)
            self.keymap.bind('j', 'Next', self.focus_next)
            self.keymap.bind('k', 'Previous', self.focus_previous)
        else:
            self.keymap.bind('left', 'Focus list', self.focus_list)
            self.keymap.bind('down', 'Next', self.focus_next)
            self.keymap.bind('up', 'Previous', self.focus_previous)

        u.register_signal(self.__class__, ['focus_list'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        widget, _ = self.walker.get_focus()


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

        widgets = []

        first_entry = True

        for key, name, *_ in record.requirements:
            if key in record.record and record.record[key]:
                if not first_entry:
                    widgets.append(EntrySeparator())

                first_entry = False

                widgets.append(EntryElement(
                    name,
                    record.record[key],
                    self.width,
                    self.keymap
                ))

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)


class App:
    "The main app."

    def __init__(self, config_path, ansi_colors=True):
        self.messenger = AppMessenger(self, ansi_colors)
        self.config = Config(self.messenger, config_path)
        self.keymap = Keymap(self.messenger)

        self.keymap.bind('q', 'Exit app', self.quit)

        self.palette = {
            ('bg', '', ''),
            ('record', '', ''),
            ('record_selected', 'black', 'dark green'),
            ('record_marked', 'white', 'dark blue'),
            ('entry_selected', 'black', 'dark green'),
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
        self.columns.set_focus(0)


    def focus_details(self):
        "Move focus to details panel."

        self.detail_view.keymap.show_hints()
        self.columns.set_focus(1)


    def update_data(self, records):
        """Render list items for each record.

        Parameters
        ----------
        records : list
        """

        self.list_view.set_data(records)


    def start(self, records):
        """Start app with records.

        Parameters
        ----------
        records : list
        """

        self.update_data(records)
        self.loop.run()
