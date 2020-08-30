import curses as cs
import textwrap as tw
import datetime


class TitleBar:

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.draw_titlebar()

    def __init__(self, window):

        self.window = window

        _, self.width = window.getmaxyx()

        self.version = 'papermate (0.1)'

        self.title = ''

    def draw_titlebar(self):

        self.window.clear()

        # program title and version  TODO grab version from setup.py
        self.window.addstr(0, 1, self.version)

        # title of article in detailedview, category in listview
        self.window.addstr(0, (self.width - len(self.title)) // 2, self.title)

        # current date
        now = datetime.datetime.now().strftime('%d-%m-%Y ')
        self.window.addstr(0, self.width - len(now) - 1, now)

        self.window.refresh()


class CommandBar:

    def __init__(self, window):
        height, width = window.getmaxyx()
        self.centre = width // 4

        self._command_size = width // 2 - 1
        self._command_win = window.derwin(1, self._command_size, 0, 0)

        self._status_size = width // 2
        self._status_win = window.derwin(1, self._status_size, 0, width // 2)

        window.bkgd('|')

        self.commands = {}
        self.status = ''

        self.draw_commands()
        self.draw_status()

        window.refresh()

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, value):
        '''dict of key and description'''

        self._commands = value
        self.draw_commands()

    def draw_commands(self):

        self._command_win.clear()

        text = '  '.join(f'{key} {desc}' for key, desc in self.commands.items())

        if len(text) >= self._command_size:
            mssg = f"commands too long for bar (max of {len(text)})"
            raise ValueError(mssg)

        x = self.centre - len(text) // 2
        for key, desc in self.commands.items():
            self._command_win.addstr(0, x, key, cs.A_STANDOUT)
            x += len(key) + 1
            self._command_win.addstr(0, x, desc)
            x += len(desc) + 2

        self._command_win.refresh()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self.draw_status()

    def draw_status(self):

        self._status_win.clear()

        x = self.centre - len(self.status) // 2

        self._status_win.addstr(0, x, self.status)
        self._status_win.refresh()


def draw_listview(window, articles):
    # TODO et al. or all authors should be in options
    window.clear()

    y = 0
    max_height, max_width = window.getmaxyx()

    for ind, article in enumerate(articles):

        width = max_width - 25
        x = 10
        y += 2

        # ----------------------------------------------------------------------
        # Numeric label
        # ----------------------------------------------------------------------

        marker = f'[{ind}] '
        window.addstr(y, x, marker)
        x += len(marker)
        width -= len(marker)

        # ----------------------------------------------------------------------
        # Title
        # ----------------------------------------------------------------------

        title = tw.wrap(article.title, width)

        title_win = window.derwin(len(title), width, y, x)

        for ind, line in enumerate(title):
            title_win.addstr(ind, 0, line, cs.A_BOLD)

        y += len(title)

        # ----------------------------------------------------------------------
        # Author
        # ----------------------------------------------------------------------

        authors = tw.wrap(article.authors[0] + ' et al.', width)

        auth_win = window.derwin(len(authors), width, y, x)

        for ind, line in enumerate(authors):
            auth_win.addstr(ind, 0, line, cs.A_DIM)

        y += len(authors)

        # ----------------------------------------------------------------------
        # Abstract
        # ----------------------------------------------------------------------

        short_abstract = tw.shorten(article.abstract, 400, placeholder='...')
        short_abstract = tw.wrap(short_abstract, width)

        abs_win = window.derwin(len(short_abstract), width, y, x)

        for ind, line in enumerate(short_abstract):
            abs_win.addstr(ind, 0, line)

        y += len(short_abstract)

    window.refresh()


def draw_detailedview(window, article):
    '''draw the detailed "more" page for a chosen article'''
    window.clear()

    x, y = 10, 2
    max_height, max_width = window.getmaxyx()
    width = max_width - 25

    # ----------------------------------------------------------------------
    # Title
    # ----------------------------------------------------------------------

    title = tw.wrap(article.title, width)

    title_win = window.derwin(len(title), width, y, x)

    for ind, line in enumerate(title):
        title_win.addstr(ind, 0, line, cs.A_BOLD)

    # ----------------------------------------------------------------------
    # Authors
    # ----------------------------------------------------------------------

    y += len(title) + 1
    x += 5
    width -= 5

    authors = tw.wrap(', '.join(article.authors), width)

    auth_win = window.derwin(len(authors), width, y, x)

    for ind, line in enumerate(authors):
        auth_win.addstr(ind, 0, line, cs.A_DIM)

    y += len(authors) + 1

    # ----------------------------------------------------------------------
    # Abstract
    # ----------------------------------------------------------------------

    abstract = tw.wrap(article.abstract, width)

    abs_win = window.derwin(len(abstract), width, y, x)

    for ind, line in enumerate(abstract):
        abs_win.addstr(ind, 0, line)

    window.refresh()
