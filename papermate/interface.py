import datetime
import curses as cs

import papermate.Article

import feedparser as fp

DEFAULT_CAT = 'astro-ph.GA'
NUM_ARTICLES = 5

COMMANDS = {
    ord('z'), ord('x'), ord('c')  # category
}

DETAILED_COMMANDS = {}

class Interface:

    def draw_titlebar(self):

        win = self.screen.subwin(1, self.width, 0, 0)

        # dunno what to put on the left
        # win.addstr(0, 0, '')

        # program title and version  TODO grab version from setup.py
        version = 'papermate (0.0.1)'
        win.addstr(0, self.width // 2, version)

        # current date
        now = datetime.datetime.now().strftime('%d-%m-%Y')
        win.addstr(0, self.width - len(now), now)

    def draw_cmdbar(self):
        '''draw from self.commands, which should be set by subclass'''
        pass

    def init_screen(self):

        self.screen.clear()

        # get info about total screen size, for sizing of windows
        self.height, self.width = self.screen.getmaxyx()

        self.draw_titlebar()

        self.draw_cmdbar()


class ListView(Interface):
    '''view of a list of articles'''

    def _get_articles(self, cat):

        # TODO if like "astro-ph", need to do OR with all subcats
        if isinstance(cat, (list, tuple, set)):
            cat = '+OR+'.join(cat)

        url = (f"http://export.arxiv.org/api/query?"
               f"search_query=cat:{cat}&"
               f"max_results={NUM_ARTICLES}&"
               f"sortBy=submittedDate")

        # TODO check for errors here
        self.articles = [papermate.Article(e) for e in fp.parse(url).entries]

    def draw_articles(self, cat=DEFAULT_CAT):

        self.clear_articles()

        win = self.screen.subwin(self.height - 3, self.width - 2, 0, 0)

        self._get_articles(cat)

        for ind, article in enumerate(self.articles):

            # TODO the 5 depends on text wrapping, figure it out
            x, y = 0, ind * 5

            marker = f'[{ind}] '

            win.addstr(y, x, marker)

            x += len(marker)

            # TODO et al. or all authors should be in options
            # TODO make sure abstract wraps correctly

            win.addstr(y, x, article.title, cs.A_BOLD)
            win.addstr(y + 1, x, article.authors[0] + ' et al.', cs.A_DIM)
            win.addstr(y + 3, x, article.abstract[:400] + '...')

    def clear_articles(self):
        '''clear the articles window'''
        pass


class DetailedView(Interface):
    '''interface for a detailed view of a single article'''

    def draw_detailed(self):
        '''draw the detailed "more" page for a chosen article'''
        pass

    def clear_detailed(self):
        pass


