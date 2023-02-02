"This is where the 'graphical' interface magic happens."

import re

import urwid as u


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

    Attributes
    ----------
    record : paperstack.data.record.Record
    """

    def __init__ (self, record, width):
        self.content = record

        title = clean_text(record.record['title'])

        self.text = u.AttrWrap(
            u.Text(title, wrap='ellipsis'),
            'record',
            'record_selected'
        )

        u.WidgetWrap.__init__(self, u.Padding(self.text, 'center', width - 1))


    def keypress(self, size, key):
        "Handle keypresses."

        return key


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
    """

    def __init__ (self, name, value, width):
        self.content = value

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

        return key


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

    Attributes
    ----------
    width : int
        Panel width.
    walker : urwid.SimpleFocusListWalker
        Walkers help reflect data onto UI elements.
    """

    def __init__(self, width):
        self.width = width

        u.register_signal(self.__class__, ['show_details'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        focus_w, _ = self.walker.get_focus()

        u.emit_signal(self, 'show_details', focus_w.content)


    def set_data(self, records):
        """Render list items for each record.

        Paramaters
        ----------
        records : list
        """

        widgets = [RecordElement(record, self.width) for record in records]

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

    Attributes
    ----------
    width : int
        Panel width.
    """

    def __init__(self, width):
        self.width = width

        u.register_signal(self.__class__, ['select_entry'])

        self.walker = u.SimpleFocusListWalker([])

        list_box = u.ListBox(self.walker)
        super().__init__(list_box)


    def modified(self):
        "When focus is modified, send signal."

        focus_w, _ = self.walker.get_focus()

        u.emit_signal(self, 'select_entry', focus_w.content)


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
                    self.width
                ))

        u.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()

        self.walker.extend(widgets)

        u.connect_signal(self.walker, 'modified', self.modified)

        self.walker.set_focus(0)


class App:
    "The main app."

    def __init__(self):
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

        list_ratio = 30
        detail_ratio = 70

        list_width = width * list_ratio // 100 - 2
        detail_width = width * detail_ratio // 100 - 2

        self.list_view = ListView(list_width)
        self.detail_view = DetailView(detail_width)

        u.connect_signal(self.list_view, 'show_details', self.show_details)

        self.footer_text = u.Text(' Q to exit')
        footer = u.AttrWrap(self.footer_text, 'footer')

        list_filler = u.Filler(
            self.list_view,
            valign = 'top',
            height = height
        )
        detail_filler = u.Filler(
            self.detail_view,
            valign = 'top',
            height = height
        )

        list_panel = u.LineBox(
            list_filler,
            title = 'Records'
        )
        detail_panel = u.LineBox(
            detail_filler,
            title = 'Details'
        )

        columns = u.Columns([
            ('weight', list_ratio, list_panel),
            ('weight', detail_ratio, detail_panel)
        ])

        frame = u.AttrMap(u.Frame(
            body = columns,
            footer = footer
        ), 'bg')

        self.loop = u.MainLoop(
            frame,
            self.palette,
            unhandled_input = self.unhandled_input
        )


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


    def unhandled_input(self, key):
        """Take care of global key bindings.

        Parameters
        ----------
        key : str
        """

        if key in ('q',):
            raise u.ExitMainLoop()


    def show_details(self, record):
        """Show record details in detail view.

        Parameters
        ----------
        record : paperstack.data.record.Record
        """

        self.detail_view.set_record(record)


    def select_entry(self, entry):
        """Select the current entry in details.

        Parameters
        ----------
        entry : paperstack.interface.app.EntryElement
        """

        pass


    def update_data(self, records):
        """Render list items for each record.

        Paramaters
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
