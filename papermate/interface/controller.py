import logging
import datetime
import curses as cs

from .interface import TitleBar, CommandBar, ListView, DetailedView
from ..queries import QuerySet, Cache


__all__ = ["controller"]


DATE_UP, DATE_DOWN = ord('x'), ord('z')
CURS_UP, CURS_DOWN = cs.KEY_UP, cs.KEY_DOWN

SELECT = (ord('\n'), ord('\r'), cs.KEY_ENTER)

BACK = (ord('b'), cs.KEY_BACKSPACE)
DOWNLOAD, ONLINE = ord('d'), ord('o')


COMMANDS = {
    'list': {
        DATE_UP, DATE_DOWN, CURS_UP, CURS_DOWN, *SELECT
    },
    'detailed': {
        DOWNLOAD, ONLINE, *BACK
    }
}

EXIT_CMDS = {
    ord('q'), 'ctrl-c', 27  # Escape key = 27, but there is a huge delay
}


def get_config_file():
    import os
    import pathlib

    datadir = f"{pathlib.Path.home()}/.config"

    fn = f"{datadir}/papermate.ini"

    try:
        # If file does not exist, create it (x mode fails if exists)
        file = open(fn, 'x')
        os.chmod(fn, 0o640)

    except FileExistsError:
        file = open(fn)

    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find/open file at {fn}")

    finally:
        file.close()

    return fn


def initialize_screen(screen):

    # get info about total screen size, for sizing of windows
    height, width = screen.getmaxyx()

    title_window = screen.subwin(1, width, 0, 0)
    titlebar = TitleBar(title_window)

    cmd_window = screen.subwin(1, width, height - 1, 0)
    cmdbar = CommandBar(cmd_window)

    border_window = screen.subwin(height - 2, width, 1, 0)
    border_window.border()
    content_window = border_window.derwin(height - 4, width - 2, 1, 1)

    logging.info(f'border size: {border_window.getmaxyx()}')
    logging.info(f'content size: {content_window.getmaxyx()}')

    screen.refresh()

    return titlebar, content_window, cmdbar


def controller(screen):
    '''designed to be used by a curses wrapper `curses.wrapper(controller)`'''

    logging.info('starting log')

    date = datetime.datetime.today()

    # ----------------------------------------------------------------------
    # Screen initialization
    # ----------------------------------------------------------------------

    cs.curs_set(0)

    titlebar, content_window, cmdbar = initialize_screen(screen)

    logging.info('Screen initialized')

    # ----------------------------------------------------------------------
    # Gather initial article list, draw initial list view
    # ----------------------------------------------------------------------

    logging.info('Loading articles')

    cmdbar.status = 'Loading articles...'

    config_file = get_config_file()
    queries = QuerySet.from_configfile(config_file)

    if len(queries) == 0:
        mssg = f"No queries found in config file {config_file}. Please add some"
        print(mssg)
        return

    search_results = queries.execute(date)

    cache = Cache({date: search_results})

    logging.info('Articles loaded')

    current_article = None

    # view = 'list'

    titlebar.title = f'Daily arXiv feed'

    cmdbar.commands = {'z/x': 'Prev/Next Day', '\u21B3': 'Select Article'}
    cmdbar.status = 'Select an article for more details'

    # draw_listview(content_window, search_results, 0)

    logging.info('Initial view drawn')

    view = ListView(content_window, date, search_results)

    logging.info(f'Heres the class:  {view}')
    logging.info(f'  {view.max_height=}, {view.max_width=}')
    logging.info(f'  {view.height=}, {view.width=}')
    logging.info(f'  {view._pages=}')

    logging.info('trying to draw it')

    # lw.draw()

    # ----------------------------------------------------------------------
    # Mainloop
    # ----------------------------------------------------------------------

    while True:

        cmd = screen.getch()

        logging.info(f'received command : {cmd} ({chr(cmd)})')

        # check that cmd is right for this view
        if cmd in COMMANDS[view.type]:

            logging.info('Command is valid')

            # commands

            # --------------------------------------------------------------
            # article select (SWITCH TO DETAILED VIEW)
            # --------------------------------------------------------------

            if cmd in SELECT:

                logging.info('Selecting article')

                current_article = search_results.articles[view.curs_ind]

                titlebar.title = f'Article Details'

                cmdbar.commands = {'d': 'Download', 'o': 'View online',
                                   'b': 'return'}
                cmdbar.status = ''

                view = DetailedView(content_window, current_article)

            # --------------------------------------------------------------
            # exit detailed (SWITCH TO LIST VIEW)
            # --------------------------------------------------------------

            elif cmd in BACK:

                logging.info('Going back')

                current_article = None

                titlebar.title = f'Daily arXiv feed'

                cmdbar.commands = {'z/x': 'Prev/Next Day',
                                   '\u21B3': 'Select Article'}

                cmdbar.status = 'Select an article for more details'

                view = ListView(content_window, date, search_results)
                # view.curs_ind =  TODO reset curs_ind to last value

            # --------------------------------------------------------------
            # Change dates
            # --------------------------------------------------------------

            elif cmd in (DATE_UP, DATE_DOWN):

                logging.info('Moving date')

                td = 1 if cmd == DATE_UP else -1
                date += datetime.timedelta(days=td)

                # Check that this date isn't in the future
                if date.date() > datetime.datetime.today().date():
                    date -= datetime.timedelta(days=td)
                    continue

                cmdbar.status = 'Loading articles...'

                if date in cache:
                    logging.info(f'reading this {date=} from cache')
                    search_results = cache[date]

                else:
                    search_results = queries.execute(date)
                    cache.cache_results(date, search_results)

                titlebar.title = f'Daily arXiv feed'
                cmdbar.status = 'Select an article for more details'

                view = ListView(content_window, date, search_results)

            # --------------------------------------------------------------
            # Scroll through articles
            # --------------------------------------------------------------

            elif cmd == CURS_UP:

                logging.info('Moving cursor up')

                view.move_cursor('up')

            elif cmd == CURS_DOWN:

                logging.info('Moving cursor down')

                view.move_cursor('down')

            # --------------------------------------------------------------
            # Commands for interacting with articles in detailed view
            # --------------------------------------------------------------

            elif cmd == DOWNLOAD:

                logging.info('Downloading file')

                cmdbar.status = 'Downloading file...'
                current_article.download()
                cmdbar.status = ''

            elif cmd == ONLINE:

                logging.info('Opening in browser')

                cmdbar.status = 'Opening in browser...'
                current_article.open_online()
                cmdbar.status = ''

        # ------------------------------------------------------------------
        # Resize terminal
        # ------------------------------------------------------------------

        elif cmd == cs.KEY_RESIZE:
            logging.info('Resizing the terminal')

            # get the base screen
            titlebar, content_window, cmdbar = initialize_screen(screen)

            # have to recreate view due to fixed content sizes at inits
            if view.type == 'list':
                view = ListView(content_window, date, search_results,
                                curs_ind=view.curs_ind, page=view.page)

            elif view.type == 'detailed':
                view = DetailedView(content_window, current_article)

        # ------------------------------------------------------------------
        # Quit program
        # ------------------------------------------------------------------

        elif cmd in EXIT_CMDS:
            # do quitty stuff
            raise SystemExit

        # some other inconsequential cmd
        else:
            continue
