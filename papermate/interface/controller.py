import logging
import datetime
import curses as cs

from .interface import TitleBar, CommandBar
from .interface import ListView, DetailedView, NoConfigView, BaseView
from ..queries import QuerySet, Cache


__all__ = ["controller"]


DATE_UP, DATE_DOWN = ord('x'), ord('z')
CURS_UP, CURS_DOWN = cs.KEY_UP, cs.KEY_DOWN
CURS_SUP, CURS_SDOWN = cs.KEY_SR, cs.KEY_SF


SELECT = (ord('\n'), ord('\r'), cs.KEY_ENTER)

BACK = (ord('b'), cs.KEY_BACKSPACE)
DOWNLOAD, ONLINE = ord('d'), ord('o')


COMMANDS = {
    'list': {
        DATE_UP, DATE_DOWN, CURS_UP, CURS_DOWN, CURS_SUP, CURS_SDOWN, *SELECT
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

    fn = f"{datadir}/papermate.toml"

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


def flash_error(screen, view, *args, titlebar=None, cmdbar=None, **kwargs):
    '''Put up a single stationary view representing an error of some sort'''

    logging.info(f'Flashing error through {view}')

    view = view(*args, **kwargs)

    if titlebar is not None:
        titlebar.title = f'ERROR - {view.title}'

    if cmdbar is not None:
        cmdbar.commands = {}
        cmdbar.status = 'Please resolve error and restart'

    # TODO doesnt handle screen resize, would be better to make part of mainloop
    while screen.getch() not in EXIT_CMDS:
        continue
    else:
        raise SystemExit


def controller(screen, mode=None):
    '''designed to be used by a curses wrapper `curses.wrapper(controller)`'''

    screen.clear()

    if mode is None:
        # bring up an options screen with each of these options available
        base_controller(screen)

    elif mode.lower() == 'daily':
        # return daily_controller()
        daily_controller(screen)

    elif mode.lower() == 'library':
        library_controller(screen)

    elif mode.lower() == 'help':
        help_controller(screen)

    elif mode.lower() == 'exit':
        raise SystemExit

    else:
        mssg = f"Unrecognized mode {mode}"
        raise ValueError(mssg)


def base_controller(screen):

    logging.info('starting log - base controller')

    # ----------------------------------------------------------------------
    # Screen initialization
    # ----------------------------------------------------------------------

    cs.curs_set(0)

    titlebar, content_window, cmdbar = initialize_screen(screen)

    titlebar.title = f''

    cmdbar.commands = {'\u21B3': 'Select mode'}
    cmdbar.status = 'Select a mode for using papermate'

    logging.info('Screen initialized')

    view = BaseView(content_window)

    while True:

        cmd = screen.getch()

        if cmd in SELECT:

            logging.info(f'Selecting Mode {view.selection}')

            controller(screen, mode=view.selection)

        elif cmd == CURS_UP:

            logging.info('Moving cursor up')

            view.move_cursor('up')

        elif cmd == CURS_DOWN:

            logging.info('Moving cursor down')

            view.move_cursor('down')

        elif cmd in EXIT_CMDS:
            raise SystemExit

        else:
            continue


def daily_controller(screen):
    '''curses controller function for the daily listing functionality'''

    logging.info('starting log - daily controller')

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
        return flash_error(screen, NoConfigView, content_window, config_file,
                           titlebar=titlebar, cmdbar=cmdbar)

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

                current_article = search_results.articles[view.selection_ind]

                titlebar.title = f'Article Details'

                cmdbar.commands = {'d': 'Download', 'o': 'View online',
                                   'b': 'return'}
                cmdbar.status = ''

                view = DetailedView(content_window, current_article,
                                    curs_ind=view.curs_ind, page=view.page)

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

                view = ListView(content_window, date, search_results,
                                curs_ind=view.curs_ind, page=view.page)

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

            elif cmd == CURS_SUP:

                logging.info('Moving page up')

                view.scroll('up', set_cursor=True)

            elif cmd == CURS_SDOWN:

                logging.info('Moving page down')

                view.scroll('down', set_cursor=True)

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

                # TODO how to stop xdg-open's stdout calls?
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


def library_controller(screen):
    pass


def help_controller(screen):
    pass
