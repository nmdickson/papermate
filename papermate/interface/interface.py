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
        now = datetime.datetime.today().strftime('%Y-%m-%d ')
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


def draw_listview(window, query_res, curs_ind):
    window.clear()

    y = 0
    max_height, max_width = window.getmaxyx()

    # 10 character buffer on either side
    width = max_width - 20

    art_ind = 0

    for query, results in query_res.items():

        x = 5
        y += 2

        window.addstr(y, x, str(query))

        x = 10

        # ------------------------------------------------------------------
        # If no articles found, note that
        # ------------------------------------------------------------------

        if results.empty:

            y += 2

            window.addstr(y, x, 'No articles found')

            continue

        # ------------------------------------------------------------------
        # List articles
        # ------------------------------------------------------------------

        for article in results:

            y += 2

            # ----------------------------------------------------------------------
            # Numeric label
            # ----------------------------------------------------------------------

            marker = f'=> ' if curs_ind == art_ind else ''
            window.addstr(y, x - len(marker), marker)
            # width -= len(marker)

            # ----------------------------------------------------------------------
            # Title
            # ----------------------------------------------------------------------

            bibcode = article.bibcode

            title = tw.wrap(article.title, width - len(bibcode) - 5)

            title_win = window.derwin(len(title), width, y, x)

            for ind, line in enumerate(title):
                title_win.addstr(ind, 0, line, cs.A_BOLD)

            title_win.addstr(0, width - len(bibcode) - 1, bibcode,
                             cs.A_UNDERLINE)

            y += len(title)

            # ----------------------------------------------------------------------
            # Author
            # ----------------------------------------------------------------------

            window.addstr(y, x, article.short_authors(width), cs.A_DIM)

            y += 1

            # ----------------------------------------------------------------------
            # Abstract
            # ----------------------------------------------------------------------

            short_abs = tw.shorten(article.abstract, 300, placeholder='...')
            short_abs = tw.wrap(short_abs, width)

            abs_win = window.derwin(len(short_abs), width, y, x)

            for ind, line in enumerate(short_abs):
                abs_win.addstr(ind, 0, line)

            y += len(short_abs)

            art_ind += 1

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
