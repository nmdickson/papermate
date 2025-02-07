import logging
import datetime
import threading
import curses as cs

from .interface import TitleBar, CommandBar
from .interface import ListView, LibraryView, DetailedView
from .interface import IntroView, NoConfigView, BaseView, ResponseErrorView
from ..queries import QuerySet, Library
from ..utils import CONFIG, get_user_libraries, create_default_library
from ..utils import prev, BidirectionalCycler, Cache, DateCache

from ads.exceptions import APIResponseError


__all__ = ["controller"]


DATE_UP = LIB_UP = ord('x')
DATE_DOWN = LIB_DOWN = ord('z')

CURS_UP, CURS_DOWN = cs.KEY_UP, cs.KEY_DOWN
CURS_SUP, CURS_SDOWN = cs.KEY_SR, cs.KEY_SF


SELECT = (ord('\n'), ord('\r'), cs.KEY_ENTER)

BACK = (ord('b'), cs.KEY_BACKSPACE)
COPY, DOWNLOAD, ONLINE, ADD_LIBRARY = ord('c'), ord('d'), ord('o'), ord('l')

# Feel like these should be stored in the views themselves, and a mapping
# function given in the views

COMMANDS = {
    'list': {
        DATE_UP, DATE_DOWN, CURS_UP, CURS_DOWN, CURS_SUP, CURS_SDOWN, *SELECT
    },
    'detailed': {
        COPY, DOWNLOAD, ONLINE, ADD_LIBRARY, *BACK
    },
    'library': {
        LIB_UP, LIB_DOWN, CURS_UP, CURS_DOWN, CURS_SUP, CURS_SDOWN, *SELECT
    }
}

EXIT_CMDS = {
    ord('q'), 'ctrl-c', 27  # Escape key = 27, but there is a huge delay
}


DEFAULT_LIBRARY = 'papermate'


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

    view = IntroView(content_window)

    # ----------------------------------------------------------------------
    # Gather initial article list, draw initial list view
    # ----------------------------------------------------------------------

    logging.info('Loading articles')

    cmdbar.status = 'Loading articles...'

    queries = QuerySet.from_configfile(CONFIG)

    if len(queries) == 0:
        return flash_error(screen, NoConfigView, content_window, CONFIG,
                           titlebar=titlebar, cmdbar=cmdbar)

    try:
        search_results = queries.execute(date)
    except APIResponseError as err:
        return flash_error(screen, ResponseErrorView, content_window,
                           err.response, titlebar=titlebar, cmdbar=cmdbar)

    cache = DateCache({date: search_results})

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
                                   'l': 'Add to library', 'b': 'return'}
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
                    logging.info("Can't move into the future, revert to today")
                    date -= datetime.timedelta(days=td)
                    continue

                # Check that this isn't a weekend we want to skip
                if CONFIG.skip_weekends and date.weekday() >= 5:
                    logging.info('Skipping over the weekend')
                    date += datetime.timedelta(days=2 * td)

                cmdbar.status = 'Loading articles...'

                if date in cache:
                    logging.info(f'reading this {date=} from cache')
                    search_results = cache[date]

                else:

                    logging.info('executing this query')

                    try:

                        if CONFIG.show_loading:
                            logging.info('starting the thread')

                            th = threading.Thread(target=queries.execute,
                                                  args=[date], daemon=True)

                            th.start()
                            logging.info('thread is running')

                            view.loading_dialog(th)

                            logging.info('thread is dead')

                        else:
                            queries.execute(date)

                    except APIResponseError as err:
                        return flash_error(screen, ResponseErrorView,
                                           content_window, err.response,
                                           titlebar=titlebar, cmdbar=cmdbar)

                    search_results = queries.results
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

                if CONFIG.show_loading:
                    logging.info('starting the thread')

                    th = threading.Thread(target=current_article.download,
                                          daemon=True)

                    th.start()
                    logging.info('thread is running')

                    view.loading_dialog(th, message='Downloading file')

                    logging.info('thread is dead')

                else:
                    current_article.download()

                cmdbar.status = ''

            elif cmd == COPY:

                logging.info('Copying bibcode to clipboard')

                cmdbar.status = 'Copying bibcode...'

                current_article.copy_bibcode()

                cmdbar.status = ''

            elif cmd == ONLINE:

                logging.info('Opening in browser')

                # TODO how to stop xdg-open's stdout calls?
                cmdbar.status = 'Opening in browser...'
                current_article.open_online()
                cmdbar.status = ''

            elif cmd == ADD_LIBRARY:

                logging.info('Adding to default library')

                cmdbar.status = 'Adding to library...'

                try:

                    if CONFIG.show_loading:
                        logging.info('starting the thread')

                        th = threading.Thread(
                            target=current_article.add_to_library,
                            daemon=True
                        )

                        th.start()
                        logging.info('thread is running')

                        view.loading_dialog(th, message='Adding to library')

                        logging.info('thread is dead')

                    else:
                        current_article.add_to_library()

                    cmdbar.status = ''

                except ValueError as err:
                    cmdbar.status = str(err)

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
    '''curses controller function for the daily listing functionality'''

    logging.info('starting log - library controller')

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

    logging.info('Loading library')

    # TODO maybe while loading blank the screen or add a loading symbol?

    cmdbar.status = 'Loading library...'

    library_map = get_user_libraries()

    if DEFAULT_LIBRARY not in library_map:
        library_map |= create_default_library()

    library_cycle = BidirectionalCycler(library_map)

    id_ = library_map[DEFAULT_LIBRARY]

    library = Library(id_)

    cache = Cache({id_: library})

    logging.info('Library loaded')

    current_article = None

    # view = 'list'

    titlebar.title = f'NASA ADS Library'

    cmdbar.commands = {'z/x': 'Prev/Next Library', '\u21B3': 'Select Article'}

    cmdbar.status = 'Select an article for more details'

    logging.info('Initial view drawn')

    view = LibraryView(content_window, library)

    logging.info(f'Heres the class:  {view}')
    logging.info(f'  {view.max_height=}, {view.max_width=}')
    logging.info(f'  {view.height=}, {view.width=}')
    logging.info(f'  {view._pages=}')

    logging.info('trying to draw it')

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

                current_article = library.articles[view.selection_ind]

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

                titlebar.title = f'NASA ADS Library'

                cmdbar.commands = {'z/x': 'Prev/Next Library',
                                   '\u21B3': 'Select Article'}

                cmdbar.status = 'Select an article for more details'

                view = LibraryView(content_window, library,
                                   curs_ind=view.curs_ind, page=view.page)

            # --------------------------------------------------------------
            # Change Library
            # --------------------------------------------------------------

            elif cmd in (LIB_UP, LIB_DOWN):

                logging.info('Moving LIB')

                mov = next if cmd == LIB_UP else prev

                cmdbar.status = 'Loading articles...'

                id_ = library_map[mov(library_cycle)]

                if date in cache:
                    logging.info(f'reading this {id_=} from cache')
                    library = cache[id_]

                else:
                    library = Library(id_)
                    cache.cache_results(id_, library)

                titlebar.title = f'NASA ADS Library'
                cmdbar.status = 'Select an article for more details'

                view = LibraryView(content_window, library,
                                   curs_ind=view.curs_ind, page=view.page)

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
                view = LibraryView(content_window, library,
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


def help_controller(screen):
    pass
