import datetime
import curses as cs

import interface

import feedparser as fp


CATEGORIES = ('astro-ph', 'astro-ph.CO', 'astro-ph.EP', 'astro-ph.GA',
              'astro-ph.HE', 'astro-ph.IM', 'astro-ph.SR')
DEFAULT_CAT = CATEGORIES[3]
NUM_ARTICLES = 5


CAT_UP, CAT_DOWN, CAT_CHOOSE = ord('z'), ord('x'), ord('c')
ART_CHOOSE = tuple(ord(str(i)) for i in range(NUM_ARTICLES))

DOWNLOAD, ONLINE = ord('d'), ord('o')
BACK = (ord('q'), cs.KEY_BACKSPACE)


COMMANDS = {
    'list': {
        CAT_UP, CAT_DOWN, CAT_CHOOSE, *ART_CHOOSE
    },
    'detailed': {
        DOWNLOAD, ONLINE, *BACK
    }
}
EXIT_CMDS = {
    'esc', 'ctrl-c'
}


class Article:

    def __init__(self, entry):
        '''`entry` is single "entries" dict from feedparser response'''

        # id
        self.id = entry.id.split('/')[-1]

        # get author names
        self.authors = [auth.name for auth in entry.authors]

        # put first author in first position
        self.authors.remove(entry.author)
        self.authors.insert(0, entry.author)

        # parse extra links
        for link in entry.links:

            if link.title == 'pdf':
                self.pdf_url = link.href

            if link.title == 'doi':
                self.doi_url = link.href

        # publishing date
        self.pub_date = entry.updated_parsed

        # abstract
        self.abstract = entry.summary.replace('\n', '')

        # title
        self.title = entry.title

    def download(self):
        pass

    def open_online(self):
        pass


def get_articles(self, cat=DEFAULT_CAT):

    # TODO if like "astro-ph", need to do OR with all subcats
    if isinstance(cat, (list, tuple, set)):
        cat = '+OR+'.join(cat)

    url = (f"http://export.arxiv.org/api/query?"
           f"search_query=cat:{cat}&"
           f"max_results={NUM_ARTICLES}&"
           f"sortBy=submittedDate")

    # TODO check for errors here
    return [Article(entry) for entry in fp.parse(url).entries]


class TitleBar:

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

        self.draw_titlebar()

    def __init__(self, window):

        self.window = window

        self.title = ''

        self.version = 'papermate (0.0.1)'

        self.draw_titlebar(window)

    def draw_titlebar(self):

        # title of article in detailedview, category in listview
        self.window.addstr(1, 0, self.title)

        # program title and version  TODO grab version from setup.py
        self.window.addstr(0, self.width // 2, self.version)

        # current date
        now = datetime.datetime.now().strftime('%d-%m-%Y ')
        self.window.addstr(0, self.width - len(now), now)

        self.window.refresh()


class CommandBar:

    def __init__(self, window):
        self.window = window
        self.draw_cmdbar()

    def draw_cmdbar(self):
        pass


def controller(screen):

    # ----------------------------------------------------------------------
    # Screen initialization
    # ----------------------------------------------------------------------

    # get info about total screen size, for sizing of windows
    height, width = screen.getmaxyx()

    title_window = screen.subwin(1, width, 0, 0)
    titlebar = TitleBar(title_window)

    cmd_window = screen.subwin(1, width, height, 0)
    cmdbar = CommandBar(cmd_window)

    content_window = screen.subwin(height - 2, width, 1, 0)

    # ----------------------------------------------------------------------
    # Gather initial article list, draw initial list view
    # ----------------------------------------------------------------------

    articles = get_articles()
    cat_ind = 3

    current_article = None

    view = 'list'

    titlebar.title = f'Articles List (cat:{DEFAULT_CAT})'

    interface.draw_listview(content_window, articles)

    # ----------------------------------------------------------------------
    # Mainloop
    # ----------------------------------------------------------------------

    while True:

        cmd = screen.getch()

        # check that cmd is right for this view
        if cmd in COMMANDS[view]:

            # commands

            # article select (SWITCH TO DETAILED VIEW)
            if cmd in ART_CHOOSE:
                view = 'detailed'

                current_article = articles[chr(cmd)]

                titlebar.title = f'Article Details'

                interface.draw_detailedview(content_window, current_article)

            # exit detailed (SWITCH TO LIST VIEW)
            elif cmd in BACK:
                view = 'list'

                current_article = None

                titlebar.title = f'Articles List (cat:{CATEGORIES[cat_ind]})'

                interface.draw_listview(content_window, articles)

            # # category changes
            # elif cmd == CAT_UP:
            #     cat_ind += 1
            # elif cmd == CAT_DOWN:
            #     cat_ind -= 1
            # elif cmd == CAT_CHOOSE:
            #     choose_category()

            # # get the article
            # elif cmd == DOWNLOAD:
            #     current_article.download()
            # elif cmd == ONLINE:
            #     current_article.open_online()

        # check if quitting
        elif cmd in EXIT_CMDS:
            # do quitty stuff
            pass

        # some other inconsequential cmd
        else:
            continue


if __name__ == '__main__':
    cs.wrapper(controller)
