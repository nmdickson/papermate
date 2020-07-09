import datetime

import article

import feedparser as fp

DEFAULT_CAT = 'astro-ph.GA'
NUM_ARTICLES = 10


class Interface():

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

    def _get_articles(self, cat):

        if isinstance(cat, (list, tuple, set)):
            cat = '+OR+'.join(cat)

        url = (f"http://export.arxiv.org/api/query?"
               f"search_query=cat:{cat}&"
               f"max_results={NUM_ARTICLES}&"
               f"sortBy=submittedDate")

        # TODO check for errors here
        self.articles = [article.Article(ent) for ent in fp.parse(url).entries]

    def draw_articles(self, cat=DEFAULT_CAT):

        # TODO clear old articles window first (if exists (eg a cat change))
        win = self.screen.subwin(self.height - 3, self.width - 2, 0, 0)

        self._get_articles(cat)

        for ind, art in enumerate(self.articles):

            # TODO the 5 depends on text wrapping, figure it out
            x, y = 0, ind * 5

            marker = f'[{ind}] '

            win.addstr(y, x, marker)

            art.draw_less(win, x + len(marker), y)

    def draw_cmdbar(self):
        pass

    def init_screen(self):

        self.screen.clear()

        # get info about total screen size, for sizing of windows
        self.height, self.width = self.screen.getmaxyx()

        self.draw_titlebar()

        self.draw_articles()

        self.draw_cmdbar()

    def mainloop(self, screen):

        self.screen = screen

        self.init_screen()

        while True:

            cmd = screen.getch()

            if cmd in COMMANDS:

                self.command(cmd)

            elif cmd in exit_cmds:
                # do quitty stuff
                pass

            else:
                continue

