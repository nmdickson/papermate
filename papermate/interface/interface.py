import curses as cs
import textwrap as tw
import datetime

import logging


def humanize_date(date, relative=True):

    out = date.strftime('%A %B %-d, %Y')

    if relative:
        diff = (datetime.datetime.today().date() - date.date()).days

        suffix = 'ago' if diff >= 0 else 'from now'

        if diff == 0:
            out += " (today)"

        elif diff == 1:
            out += " (yesterday)"

        else:
            out += f" ({diff} days {suffix})"

    return out


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

        self.version = 'papermate (1.0)'

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


class ListView:

    type = 'list'

    @property
    def selection_ind(self):
        return sum(self.Narticles[:self.page]) + self.curs_ind

    def __init__(self, window, date, query_res, *, curs_ind=0, page=0,
                 show_query_col=True):

        self.window = window

        self.window.clear()

        self.date_title = humanize_date(date)

        self.max_height, self.max_width = self.window.getmaxyx()

        self.margin_width = int(0.1 * self.max_width)
        self.query_col_width = self.margin_width if show_query_col else 0
        self.width = self.max_width - (2 * (self.margin_width + 4))

        # self.height, self.width = self.max_height - 2, self.max_width - 20
        # self.height = self.max_height - 2
        self.height = self.max_height

        self.curs_ind = curs_ind
        self.page = page

        self._query_res = query_res

        # for each query, get all the actual text and stuff involved
        # and figure out how many lines total are in it, so we can decide what
        # to show on each page
        self._pages, self.Narticles = [], []
        content = {}
        Nline = 2
        for query, results in query_res.items():

            logging.info(f'creating view for {query=}')

            if results.empty:
                Nline += 2

                if Nline < self.height:
                    content[query] = None

                else:
                    self.Narticles.append(sum([len(arts) if arts else 0
                                               for arts in content.values()]))

                    self._pages.append(content)

                    content = {query: None}
                    # Nline = 2 + para['Nlines'] + 2

                continue

            content[query] = []

            for article in results:

                logging.info(f'--creating view for {article=}')

                para = {}

                title_width = self.width - len(article.bibcode) - 5
                para['title'] = tw.wrap(article.title, title_width)

                para['abstract'] = article.short_abstract(self.width)

                para['Nlines'] = sum(map(len, para.values())) + 1

                para['authors'] = article.short_authors(self.width)
                para['bibcode'] = article.bibcode

                Nline += para['Nlines'] + 2

                logging.info(f'---- lines: {para["Nlines"]} '
                             f'({Nline} / {self.height} total)')

                # logging.info(f'{content=}')
                # logging.info(content[query])

                if Nline < self.height:
                    logging.info('---- adding this para to content')
                    content[query].append(para)

                else:
                    # move to a new page
                    logging.info('---- starting new page')

                    if not content[query]:
                        del content[query]

                    self.Narticles.append(sum([len(arts) if arts else 0
                                               for arts in content.values()]))

                    self._pages.append(content)

                    content = {query: [para]}
                    Nline = 2 + para['Nlines'] + 2

        self.Narticles.append(sum([len(arts) if arts else 0
                                   for arts in content.values()]))
        self._pages.append(content)

        self.Npages = len(self._pages)

        self.draw()

    def draw(self):
        '''draw this page'''

        self.window.clear()

        logging.info(f'drawing page {self.page} (cursor {self.curs_ind})')

        content = self._pages[self.page]

        logging.info(f'--drawing {content}')

        self.window.addstr(1, (self.max_width - len(self.date_title)) // 2,
                           self.date_title, cs.A_ITALIC)

        y = 3

        art_ind = 0

        page_label = f'pg. {self.page + 1}/{self.Npages}'
        self.window.addstr(y, self.max_width - len(page_label) - 2,
                           page_label, cs.A_ITALIC)

        for query, articles in content.items():

            logging.info(f'---- drawing {query=}')

            x = 4
            # y += 2

            logging.info('---- drawing query name in column')

            # window.addstr(y, x, str(query))
            for dy, line in enumerate(query.column_str(self.query_col_width)):
                xi = self.query_col_width - len(line)
                self.window.addstr(y + dy, xi, line, cs.A_ITALIC)

            x = self.margin_width + (2 * 4)

            # --------------------------------------------------------------
            # If no articles found, note that
            # --------------------------------------------------------------

            if articles is None:

                # y += 2

                self.window.addstr(y, x, 'No articles found')

                y += 3

                continue

            # --------------------------------------------------------------
            # List articles
            # --------------------------------------------------------------

            for para in articles:

                logging.info(f'------ drawing article {para}')

                # y += 2

                # ----------------------------------------------------------
                # Numeric label
                # ----------------------------------------------------------

                marker = f'=> ' if self.curs_ind == art_ind else ''
                self.window.addstr(y, x - len(marker), marker)
                # width -= len(marker)

                # ----------------------------------------------------------
                # Title
                # ----------------------------------------------------------

                # bibcode = para['bibcode']

                # title = tw.wrap(para['title'], width - len(bibcode) - 5)

                title_win = self.window.derwin(len(para['title']),
                                               self.width + 1, y, x)

                for ind, line in enumerate(para['title']):
                    title_win.addstr(ind, 0, line, cs.A_BOLD)

                title_win.addstr(0, self.width - len(para['bibcode']),
                                 para['bibcode'], cs.A_UNDERLINE)

                y += len(para['title'])

                # ----------------------------------------------------------
                # Author
                # ----------------------------------------------------------

                self.window.addstr(y, x, para['authors'], cs.A_DIM)

                y += 1

                # ----------------------------------------------------------
                # Abstract
                # ----------------------------------------------------------

                abs_win = self.window.derwin(len(para['abstract']), self.width,
                                             y, x)

                for ind, line in enumerate(para['abstract']):
                    try:
                        abs_win.addstr(ind, 0, line)
                    except cs.error:
                        pass

                y += len(para['abstract'])

                art_ind += 1

                y += 2

        self.window.refresh()

    def scroll(self, direction, *, strict=False, redraw=True, set_cursor=False):
        '''scroll this page up or down'''

        if direction == 'up':

            self.page -= 1

            if set_cursor:
                self.curs_ind = 0

            if self.page < 0:

                self.page = 0

                if strict:
                    mssg = f'Hitting upper bound (page={self.page})'
                    raise RuntimeError(mssg)

        elif direction == 'down':

            self.page += 1

            if set_cursor:
                self.curs_ind = 0

            if self.page >= self.Npages:

                self.page = self.Npages - 1

                if strict:
                    mssg = f'Hitting lower bound (page={self.page})'
                    raise RuntimeError(mssg)

                if set_cursor:
                    self.curs_ind = self.Narticles[self.page] - 1

        if redraw:
            self.draw()

    def move_cursor(self, direction, *, redraw=True):
        '''move the cursor up or down'''

        # TODO really sucks to redraw the entire window each time

        if direction == 'up':

            self.curs_ind -= 1

            if self.curs_ind < 0:

                try:
                    self.scroll('up', strict=True, redraw=False)
                    # Narticles = sum(map(len, self._pages[self.page].values()))

                    self.curs_ind = self.Narticles[self.page] - 1

                except RuntimeError:
                    self.curs_ind = 0

        elif direction == 'down':

            self.curs_ind += 1

            # number of articles on this page
            # Narticles = sum(map(len, self._pages[self.page].values()))

            if self.curs_ind >= self.Narticles[self.page]:

                try:
                    self.scroll('down', strict=True, redraw=False)
                    self.curs_ind = 0

                except RuntimeError:
                    self.curs_ind = self.Narticles[self.page] - 1

        if redraw:
            self.draw()


class LibraryView(ListView):

    type = 'library'

    def __init__(self, window, library, *, curs_ind=0, page=0):
        date = datetime.datetime.today()

        self.title = f'{library.name}'

        super().__init__(window, date, {library.query.id: library},
                         curs_ind=curs_ind, page=page, show_query_col=False)

    def draw(self):
        '''draw this page'''

        self.window.clear()

        logging.info(f'drawing page {self.page} (cursor {self.curs_ind})')

        content = self._pages[self.page]

        logging.info(f'--drawing {content}')

        self.window.addstr(1, (self.max_width - len(self.title)) // 2,
                           self.title, cs.A_ITALIC)

        x, y = self.margin_width + 4, 3

        art_ind = 0

        page_label = f'pg. {self.page + 1}/{self.Npages}'
        self.window.addstr(y, self.max_width - len(page_label) - 2,
                           page_label, cs.A_ITALIC)

        for articles in content.values():

            # --------------------------------------------------------------
            # If no articles found, note that
            # --------------------------------------------------------------

            if articles is None:

                self.window.addstr(y, x, 'No articles found')

                y += 3

                continue

            # --------------------------------------------------------------
            # List articles
            # --------------------------------------------------------------

            for para in articles:

                logging.info(f'------ drawing article {para}')

                # ----------------------------------------------------------
                # Numeric label
                # ----------------------------------------------------------

                marker = f'=> ' if self.curs_ind == art_ind else ''
                self.window.addstr(y, x - len(marker), marker)

                # ----------------------------------------------------------
                # Title
                # ----------------------------------------------------------

                title_win = self.window.derwin(len(para['title']),
                                               self.width + 1, y, x)

                for ind, line in enumerate(para['title']):
                    title_win.addstr(ind, 0, line, cs.A_BOLD)

                title_win.addstr(0, self.width - len(para['bibcode']),
                                 para['bibcode'], cs.A_UNDERLINE)

                y += len(para['title'])

                # ----------------------------------------------------------
                # Author
                # ----------------------------------------------------------

                self.window.addstr(y, x, para['authors'], cs.A_DIM)

                y += 1

                # ----------------------------------------------------------
                # Abstract
                # ----------------------------------------------------------

                abs_win = self.window.derwin(len(para['abstract']), self.width,
                                             y, x)

                for ind, line in enumerate(para['abstract']):
                    try:
                        abs_win.addstr(ind, 0, line)
                    except cs.error:
                        pass

                y += len(para['abstract'])

                art_ind += 1

                y += 2

        self.window.refresh()


class DetailedView:

    type = 'detailed'

    def __init__(self, window, article, *, curs_ind=0, page=0):

        self.window = window
        self.article = article

        # optionally store this articles position for outside use
        self.curs_ind = curs_ind
        self.page = page

        self.window.clear()

        self.max_height, self.max_width = self.window.getmaxyx()

        self.height = self.max_height
        self.margin_width = int(0.1 * self.max_width)  # i.e. query_col_width
        self.width = self.max_width - (2 * (self.margin_width + 4))

        self.abs_width = self.width - 5

        self.draw()

    def draw(self):

        x, y = self.margin_width, 2

        # ------------------------------------------------------------------
        # Title
        # ------------------------------------------------------------------

        title = self.article.wrap_property('title', self.width)

        title_win = self.window.derwin(len(title), self.width, y, x)

        for ind, line in enumerate(title):
            title_win.addstr(ind, 0, line, cs.A_BOLD)

        # ------------------------------------------------------------------
        # Authors
        # ------------------------------------------------------------------

        y += len(title) + 1
        x += 5

        # TODO how to handle when way too long and content wont fit screen?
        authors = self.article.wrap_property('authors', self.abs_width)

        affils = self.article.wrap_property('affiliations', self.abs_width)

        auth_win = self.window.derwin(
            len(authors) + len(affils) + 1, self.abs_width,
            y, x
        )

        for ind, line in enumerate(authors):
            auth_win.addstr(ind, 0, line, cs.A_ITALIC)

        for ind, line in enumerate(affils, len(authors)):
            auth_win.addstr(ind, 0, line, cs.A_DIM)

        auth_win.addstr(len(authors) + len(affils), 0,
                        self.article.date, cs.A_DIM)

        y += len(authors) + len(affils) + 1 + 1

        # ------------------------------------------------------------------
        # Abstract
        # ------------------------------------------------------------------

        abstract = self.article.wrap_property('abstract', self.abs_width)

        abs_win = self.window.derwin(len(abstract), self.abs_width, y, x)

        for ind, line in enumerate(abstract):

            try:
                abs_win.addstr(ind, 0, line)
            except cs.error:
                # just in case, because curses can't write to lower-right corner
                pass

        y += len(abstract) + 1

        # ------------------------------------------------------------------
        # Infobox
        # ------------------------------------------------------------------

        info = []

        # bibcode
        info += self.article.wrap_property('bibcode', self.abs_width,
                                           label=True)

        # doi
        info += self.article.wrap_property('doi', self.abs_width,
                                           label=True)

        # bibstem
        info += self.article.wrap_property('bibstem', self.abs_width,
                                           label=True)

        # page
        info += self.article.wrap_property('page', self.abs_width,
                                           label=True)

        # read_count
        info += self.article.wrap_property('read_count', self.abs_width,
                                           label=True)

        logging.info(info)

        info_width = max(map(len, info)) + 4
        info_height = len(info) + 4

        logging.info(f'{len(info)=}, {info_width=}, {y=}, {x=}')

        y = self.height - info_height - 1
        info_win = self.window.derwin(info_height, info_width, y, x)

        for ind, line in enumerate(info, 2):
            info_win.addstr(ind, 2, line)

        info_win.border()
        info_win.addstr(0, 1, 'INFO')

        self.window.refresh()


class BaseView:

    @property
    def selection(self):
        return self.options[self.curs_ind]

    def __init__(self, window):

        self.window = window

        self.curs_ind = 0

        self.window.clear()

        self.max_height, self.max_width = self.window.getmaxyx()

        self.height = self.max_height
        self.width = self.max_width

        self.options = ("Daily", "Library", "Help", "Exit")

        self.draw()

    def draw(self):

        # in the middle of the screen, draw 4 boxes ("buttons"), one
        # for each possible mode (daily, library, help) and for "quit"

        button_height = 5
        button_width = 17

        x = (self.width - button_width) // 2
        y = (self.height - (button_height * len(self.options))) // 2 - 1

        # Draw squares
        for ind, lbl in enumerate(self.options):

            button_win = self.window.derwin(button_height, button_width, y, x)

            button_win.border()

            lbl_x = (((button_width - 2) - len(lbl)) // 2) + 1

            button_win.addstr(2, lbl_x, lbl)

            if ind == self.curs_ind:
                for yi in range(1, 4):
                    button_win.addch(yi, 0, ">")
                    button_win.addch(yi, button_width - 1, "<")

            y += ((button_height + 1))

        self.window.refresh()

    def move_cursor(self, direction):
        '''move the cursor up or down'''

        # TODO really sucks to redraw the entire window each time

        if direction == 'up':

            self.curs_ind = max(0, self.curs_ind - 1)

        elif direction == 'down':

            self.curs_ind = min(len(self.options) - 1, self.curs_ind + 1)

        self.draw()


class ErrorView:

    type = 'error'

    title = 'Error'
    message = 'Error message'

    def __init__(self, window):

        self.window = window

        self.window.clear()

        max_height, max_width = self.window.getmaxyx()

        self.height = max_height
        self.width = max_width - (2 * 4)

        self.draw()

    def draw(self):
        import textwrap as tw

        # Split message on newlines and wrap, if necessary
        # for fully empty lines, place whitespace between two "\n \n" in message

        mssg = self.message.split('\n')
        wrap_mssg = sum(
            [tw.wrap(s, self.width, drop_whitespace=False) for s in mssg], []
        )

        y = (self.height - len(wrap_mssg)) // 2

        # Write out each line, centre-aligned as possible

        for ind, line in enumerate(wrap_mssg, y):
            x = 4 + (self.width - len(line)) // 2
            self.window.addstr(ind, x, line, cs.A_BOLD)

        # refresh screen

        self.window.refresh()


class NoConfigView(ErrorView):

    @property
    def title(self):
        return "Empty Config File"  # get autocreated so it's empty, not missing

    @property
    def message(self):
        mssg = (f'No queries were found in the papermate config file at '
                f'"{self.config_file}"\n \n'
                f"Please add at least one query. "
                f"See documentation for examples")
        return mssg

    def __init__(self, window, config_file):
        self.config_file = config_file
        super().__init__(window=window)
