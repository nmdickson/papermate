import curses as cs
import textwrap as tw
import datetime

import logging


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


class ListView:

    type = 'list'

    def __init__(self, window, query_res):

        self.window = window

        self.window.clear()

        self.max_height, self.max_width = self.window.getmaxyx()

        self.query_col_width = int(0.1 * self.max_width)
        self.width = self.max_width - (2 * (self.query_col_width + 4))

        # self.height, self.width = self.max_height - 2, self.max_width - 20
        # self.height = self.max_height - 2
        self.height = self.max_height

        self.curs_ind = 0
        self.page = 0

        self._query_res = query_res

        # for each query, get all the actual text and stuff involved
        # and figure out how many lines total are in it, so we can decide what
        # to show on each page
        self._pages, self.Narticles = [], []
        content = {}
        Nline = 2
        for query, results in query_res.items():

            logging.info(f'creating view for {query=}')

            content[query] = []

            if results.empty:
                Nline += 2
                content[query] = None

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

        logging.info(f'drawing page {self.page}')

        content = self._pages[self.page]

        logging.info(f'--drawing {content}')

        y = 2
        # max_height, max_width = self.window.getmaxyx()

        # query_col_width = 30
        # self.query_col_width = int(0.1 * max_width)

        # 10 character buffer on either side
        # width = max_width - 20
        # width = max_width - (2 * (query_col_width + 4))

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

            x = self.query_col_width + (2 * 4)

            # ------------------------------------------------------------------
            # If no articles found, note that
            # ------------------------------------------------------------------

            if articles is None:

                # y += 2

                self.window.addstr(y, x, 'No articles found')

                y += 3

                continue

            # ------------------------------------------------------------------
            # List articles
            # ------------------------------------------------------------------

            for para in articles:

                logging.info(f'------ drawing article {para}')

                # y += 2

                # ----------------------------------------------------------------------
                # Numeric label
                # ----------------------------------------------------------------------

                marker = f'=> ' if self.curs_ind == art_ind else ''
                self.window.addstr(y, x - len(marker), marker)
                # width -= len(marker)

                # ----------------------------------------------------------------------
                # Title
                # ----------------------------------------------------------------------

                logging.info(f'------ drawing article title')

                # bibcode = para['bibcode']

                # title = tw.wrap(para['title'], width - len(bibcode) - 5)

                logging.info(f'-------- height={len(para["title"])}, '
                             f'width={self.width}, {y=}, {x=}')

                title_win = self.window.derwin(len(para['title']),
                                               self.width + 1, y, x)

                for ind, line in enumerate(para['title']):

                    logging.info(f'-------- y={ind}, x={0}, '
                                 f'{len(line)=}, {line=}')

                    title_win.addstr(ind, 0, line, cs.A_BOLD)

                title_win.addstr(0, self.width - len(para['bibcode']),
                                 para['bibcode'], cs.A_UNDERLINE)

                y += len(para['title'])

                # ----------------------------------------------------------------------
                # Author
                # ----------------------------------------------------------------------

                logging.info(f'------ drawing article author')

                self.window.addstr(y, x, para['authors'], cs.A_DIM)

                y += 1

                # ----------------------------------------------------------------------
                # Abstract
                # ----------------------------------------------------------------------

                logging.info(f'------ drawing article abstract')
                logging.info(f'-------- height={len(para["abstract"])}, '
                             f'width={self.width}, {y=}, {x=}')

                # short_abs = tw.shorten(article.abstract, 300, placeholder='...')
                # short_abs = tw.wrap(short_abs, width)

                abs_win = self.window.derwin(len(para['abstract']), self.width + 1,
                                             y, x)

                for ind, line in enumerate(para['abstract']):
                    logging.info(f'-------- y={ind}, x={0}, '
                                 f'{len(line)=}, {line=}')
                    abs_win.addstr(ind, 0, line)

                y += len(para['abstract'])

                art_ind += 1

                y += 2

        self.window.refresh()

    def scroll(self, direction, *, strict=False, redraw=True):
        '''scroll this page up or down'''

        if direction == 'up':

            self.page -= 1

            if self.page < 0:

                self.page = 0

                if strict:
                    mssg = f'Hitting upper bound (page={self.page})'
                    raise RuntimeError(mssg)

        elif direction == 'down':

            self.page += 1

            if self.page >= self.Npages:

                self.page = self.Npages - 1

                if strict:
                    mssg = f'Hitting lower bound (page={self.page})'
                    raise RuntimeError(mssg)

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


class DetailedView:

    type = 'detailed'

    def __init__(self, window, article):

        self.window = window
        self.article = article

        self.window.clear()

        self.max_height, self.max_width = self.window.getmaxyx()

        self.query_col_width = int(0.1 * self.max_width)
        self.width = self.max_width - (2 * (self.query_col_width + 4))

        self.abs_width = self.width - 5

        self.draw()

    def draw(self):

        x, y = 10, 2

        # ----------------------------------------------------------------------
        # Title
        # ----------------------------------------------------------------------

        title = tw.wrap(self.article.title, self.width)

        title_win = self.window.derwin(len(title), self.width, y, x)

        for ind, line in enumerate(title):
            title_win.addstr(ind, 0, line, cs.A_BOLD)

        # ----------------------------------------------------------------------
        # Authors
        # ----------------------------------------------------------------------

        y += len(title) + 1
        x += 5

        authors = tw.wrap(', '.join(self.article.authors), self.abs_width)

        auth_win = self.window.derwin(len(authors), self.abs_width, y, x)

        for ind, line in enumerate(authors):
            auth_win.addstr(ind, 0, line, cs.A_DIM)

        y += len(authors) + 1

        # ----------------------------------------------------------------------
        # Abstract
        # ----------------------------------------------------------------------

        abstract = tw.wrap(self.article.abstract, self.abs_width)

        abs_win = self.window.derwin(len(abstract), self.abs_width, y, x)

        for ind, line in enumerate(abstract):
            abs_win.addstr(ind, 0, line)

        self.window.refresh()
