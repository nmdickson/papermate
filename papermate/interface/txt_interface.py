import datetime
import curses as cs
import time
import enum
import logging
import textwrap as tw
from curses import panel

from textual.widget import Widget
from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.binding import Binding
from textual.message import Message
from textual import widgets, containers, on, work
from textual.containers import Horizontal, Vertical, Center

from ..utils import CONFIG, READMARKERS

from ..queries import QuerySet, Library, QuerySetResult
from ..utils import CONFIG, get_user_libraries, create_default_library
from ..utils import prev, BidirectionalCycler, Cache, DateCache

from .txt_widgets import ContentWindow, QRCode, TripleHeader, DateLoadingIndicator, DateSelectModal


__all__ = ["ChangeView", "CacheResults", "BaseView", "ListView", "LibraryView",
           "DetailedView", "ErrorView", "Controller"]

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


CACHE = DateCache()


def humanize_date(date: datetime.date, relative: bool = True) -> str:

    out = date.strftime('%A %B %-d, %Y')

    if relative:
        diff = (datetime.date.today() - date).days

        suffix = 'ago' if diff >= 0 else 'from now'

        if diff == 0:
            out += " (today)"

        elif diff == 1:
            out += " (yesterday)"

        else:
            out += f" ({diff} days {suffix})"

    # TODO right align this
    if CONFIG.mark_read:
        out += f' [{"R" if date in READMARKERS else " "}]'

    return out


class ChangeView(Message):
    '''Message to change this view'''
    def __init__(self, to_view, view_args=None):
        super().__init__()
        self.to_view = to_view
        self.view_args = view_args


class PreviousView(Message):
    '''Message to change this view'''
    pass


class CacheResults(Message):
    '''Message to add query results to the cache'''
    def __init__(self, date, query_results: QuerySetResult):
        super().__init__()
        self.date = date
        self.query_results = query_results


class ScreenReady(Message):
    pass
    # '''Message to change this view'''
    # def __init__(self):
    #     super().__init__()
    #     self.to_view = to_view
    #     self.view_args = view_args



# --------------------------------------------------------------------------
# Base papermate menu
# --------------------------------------------------------------------------


class SplashScreen(ContentWindow):

    def compose(self):
        with Center():
            yield widgets.Static('SPLASH SCREEN')

    def on_mount(self) -> None:
        self.post_message(ScreenReady())


class BaseView(ContentWindow):

    class Exit(Message):
        pass

    @on(widgets.Button.Pressed, "#daily")
    def daily_pressed(self, event: widgets.Button.Pressed) -> None:
        # self.post_message(ChangeView(ListView, [datetime.datetime.today() - datetime.timedelta(5)]))
        self.post_message(ChangeView(ListView, [datetime.date.today()]))

    @on(widgets.Button.Pressed, "#library")
    def library_pressed(self, event: widgets.Button.Pressed) -> None:
        self.post_message(ChangeView(LibraryView))

    @on(widgets.Button.Pressed, "#exit")
    def exit_pressed(self, event: widgets.Button.Pressed) -> None:
        self.post_message(self.Exit())

    def compose(self):
        with Center():
            yield widgets.Button("Daily", id="daily")
            yield widgets.Button("Library", id="library")
            yield widgets.Button("Help", id="help")
            yield widgets.Button("Exit", id='exit')


# --------------------------------------------------------------------------
# Article listing modes
# --------------------------------------------------------------------------


class ArticleSummary(Widget, can_focus=True):
    '''
    the title, authors, abstract, bibcode, in a few lines
    to make up:

    focusable (show an arrow on the left when focused?)
    pressable (post message indicating change view to detailed view)

    article is Article, as given by a QueryResult, as given by a QueryResultSet

    style in tcss file. style widths and heights are important for layout
    they should be in the reqd file
    '''

    BINDINGS = [Binding("enter", "select", "select article")]

    FOCUS_ON_CLICK = False

    def __init__(self, article, query_name):
        super().__init__()

        self.article = article

        self.query_col = widgets.Static(query_name, id='query-name')
        self.indicator = widgets.Static("=>", id='article-indicator')

        self.title = widgets.Static(article.title, id="article-title")
        self.bibcode = widgets.Static(article.bibcode, id="article-bibcode")
        self.author = widgets.Static(article.short_authors, id='article-short-author')
        self.abstract = widgets.Static(article.short_abstract, id='article-short-abstract')

    def compose(self):

        with Horizontal():
            yield self.query_col
            yield self.indicator
            with Vertical():
                with Horizontal():
                    yield self.title
                    yield self.bibcode

                yield self.author
                yield self.abstract

    def on_click(self, event):
        self.action_select()

    def action_select(self):
        self.post_message(ChangeView(DetailedView, [self.article]))

    def on_enter(self, event):
        '''focus when the mouse enters this article'''
        self.focus()


class EmptySummary(Widget, can_focus=True):
    '''
    articlesummary when there are none
    '''

    # BINDINGS = [Binding("enter", "select", "select article")]

    FOCUS_ON_CLICK = False

    def __init__(self, query_name):
        super().__init__()


        self.query_col = widgets.Static(query_name, id='query-name')
        self.indicator = widgets.Static("=>", id='article-indicator')

        self.title = widgets.Static("No articles found", id="article-title")
        # self.bibcode = widgets.Static(article.bibcode, id="article-bibcode")
        # self.author = widgets.Static(article.short_authors, id='article-short-author')
        # self.abstract = widgets.Static(article.short_abstract, id='article-short-abstract')

    def compose(self):

        with Horizontal():
            yield self.query_col
            yield self.indicator
            with Vertical():
                with Horizontal():
                    yield self.title
                    # yield self.bibcode

                # yield self.author
                # yield self.abstract

    # def on_click(self, event):
    #     self.action_select()

    # def action_select(self):
    #     self.post_message(ChangeView(DetailedView, [self.article]))

    # def on_enter(self, event):
    #     '''focus when the mouse enters this article'''
    #     self.focus()


class QueryList(Widget):

    def __init__(self, query, results):
        super().__init__()

        self.queryobj = query  # dont stomp on widget namespaces
        self.results = results

        self.N = len(results)

    def compose(self):
        if self.N > 0:
            for article in self.results:
                yield ArticleSummary(article, query_name=self.queryobj.column_str)
        else:

            # TODO this need serious work, nothing at all shows up now
            yield EmptySummary(query_name=self.queryobj.column_str)


class ListView(ContentWindow):
# class ListView(ContentWindow, can_focus=True):

    # TODO if there are no articles, nothing focus, no bindings, and youre stuck
    BINDINGS = [
        Binding(key='q', action='quit', description='Exit'),
        Binding(key='up', action='up', description='up'),
        Binding(key='down', action='down', description='down'),
        Binding(key='shift+up', action='up_five', show=False),
        Binding(key='shift+down', action='down_five', show=False),
        Binding(key='z', action='prev_date', description='Prev. day'),
        Binding(key='x', action='next_date', description='Next day'),
        Binding(key='g', action='goto_date', description='goto date'),
    ]

    def __init__(self, date: datetime.date):
        super().__init__()

        self.date = date
        self.title = humanize_date(date, CONFIG.show_relative_date)

        self.queries = QuerySet.from_configfile(CONFIG)

    @work
    async def execute_and_mount_query(self):

        self.loading = True

        await self.queries.execute(self.date)
        self.query_res = self.queries.results

        self.post_message(CacheResults(self.date, self.query_res))

        self.loading = False

        for query, results in self.query_res.items():
            self.mount(QueryList(query, results))

        # TODO also need to keep focussed article when doing "back" from details
        self._focus_on_first()

        return self.query_res

    def compose(self):

        yield widgets.Static(self.title, id='date-title')

        # TODO I actually hate the scroll, pagination is better

        # TODO for some reason there is a notable delay loading caches
        if self.date in CACHE:
            self.query_res = CACHE[self.date]

            logging.info(f'reading this {self.date=} from cache')
            for query, results in self.query_res.items():
                yield QueryList(query, results)

    def on_mount(self):

        if self.date not in CACHE:
            logging.info(f'executing query for {self.date=}')
            qr = self.execute_and_mount_query()

        else:
            self._focus_on_first()

    def _focus_on_first(self):
        try:
            self.query('ArticleSummary').first().focus()
        except NoMatches:
            self.query('EmptySummary').first().focus()

    def get_loading_widget(self):
        return DateLoadingIndicator(humanize_date(self.date, False))

    def change_date(self, td: int):
        new_date = self.date + datetime.timedelta(days=td)

        # Check that this isn't a weekend we want to skip
        # TODO if you start on a sunday and hit back, you'll go to thursday
        if CONFIG.skip_weekends and new_date.weekday() >= 5:
            logging.info('Skipping over the weekend')
            new_date += datetime.timedelta(days=2 * td)

        self.post_message(ChangeView(ListView, [new_date,]))

    def action_prev_date(self):
        self.change_date(td=-1)

    def action_next_date(self):
        self.change_date(td=1)

    def action_up(self):
        self.screen.focus_previous()

    def action_down(self):
        self.screen.focus_next()

    def action_up_five(self):
        for _ in range(5):
            self.screen.focus_previous()

    def action_down_five(self):
        for _ in range(5):
            self.screen.focus_next()

    def action_goto_date(self) -> None:

        def post_goto(new_date) -> None:
            self.post_message(ChangeView(ListView, [new_date,]))

        self.app.push_screen(DateSelectModal(), post_goto)


class LibraryView(ListView):

    # TODO

    # library_map = get_user_libraries()

    # if DEFAULT_LIBRARY not in library_map:
    #     library_map |= create_default_library()

    # library_cycle = BidirectionalCycler(library_map)

    # id_ = library_map[DEFAULT_LIBRARY]

    # library = Library(id_)

    # cache = Cache({id_: library})


    def __init__(self, library: Library):
        date = datetime.date.today()

        self.title = f'{library.name}'

        # TODO should be removing the query_col, might error until then
        super().__init__(date, {library.query.id: library})


# --------------------------------------------------------------------------
# Article details mode
# --------------------------------------------------------------------------


class ArticleDetails(Widget):

    def __init__(self, article):
        super().__init__()

        self.article = article

        self.title = widgets.Static(article.title, id="article-title")
        self.authors = widgets.Static(article.authors, id='article-author')
        self.affiliations = widgets.Static(article.affiliations, id='article-affl')
        self.date = widgets.Static(article.date, id='article-date')
        self.abstract = widgets.Static(article.abstract, id='article-abstract')

    def compose(self):

        with Vertical():
            yield self.title
            yield self.authors
            yield self.affiliations
            yield self.date
            yield self.abstract


class InfoBox(Widget):

    BORDER_TITLE = "INFO"

    def __init__(self, article):
        super().__init__()

        self.bibcode = widgets.Static(f"bibcode = {article.bibcode}", classes="info-entries")
        self.doi = widgets.Static(f"doi = {article.doi}", classes="info-entries")
        self.bibstem = widgets.Static(f"bibstem = {article.bibstem}", classes="info-entries")
        self.page = widgets.Static(f"page = {article.page}", classes="info-entries")
        self.read_count = widgets.Static(f"read_count = {article.read_count}", classes="info-entries")

    def compose(self):

        with Vertical():
            yield self.bibcode
            yield self.doi
            yield self.bibstem
            yield self.page
            yield self.read_count


class DetailedView(ContentWindow, can_focus=True):

    BINDINGS = [
        Binding("b", "back", "Back"),
        Binding("o", "open", "Open article"),
        Binding("d", "download", "Download article"),
        Binding("c", "copy", "Copy bibcode"),
        Binding("l", "library", "Add to library"),
    ]

    def __init__(self, article) -> None:
        super().__init__()

        self.article = article

    def compose(self):

        with Center():
            yield ArticleDetails(self.article)

        with Horizontal(id="bottom-info"):
            yield InfoBox(self.article)
            yield widgets.Placeholder(id='spacer')
            yield QRCode(self.article.url, inverse=True)

    def action_back(self):
        # TODO need to focus the same article
        self.post_message(PreviousView())

    def action_open(self):
        # TODO for some reason there is a big delay on these actions?
        self.article.open_online()

    def action_download(self):
        # TODO add loading splash here while downloading
        self.article.download()

    def action_copy(self):
        self.article.copy_bibcode()

    def action_library(self):
        # TODO add loading splash here while adding
        self.article.add_to_library()


# --------------------------------------------------------------------------
# Error handling modes
# --------------------------------------------------------------------------


class ErrorView(ContentWindow):

    title = 'Error'
    message = 'Error message'

    def render(self):
        return f"[bold]{self.title}[/bold]\n\n{self.message}"

    # def on_mount(self):
    #     # TODO change the title in the titlebar to this title
    #     #   may require passing meassge up to app actually
    #     return super().on_mount()


class NoConfigView(ErrorView):

    title = "Empty Config File"  # get autocreated so it's empty, not missing

    def __init__(self, config_file):
        super().__init__()

        self.message = (
            f'No queries were found in the papermate config file at '
            f'"{config_file}"\n \n'
            f"Please add at least one query. "
            f"See documentation for examples."
        )


class ResponseErrorView(ErrorView):

    title = "ADS API Response Error"

    _default_tip = "turning it off and on again?"

    _tip_library = {
        404: 'complaining to Nolan that he somehow messed up the query url?',
        418: 'not brewing coffee in a teapot?',
        429: ('checking your ADS API rate limit?\n'
              'See ads.readthedocs.io/en/latest/index.html#rate-limit-usage.'),
        500: _default_tip,
        502: _default_tip,
        503: 'checking if "adsabs.harvard.edu" is live?'
    }

    def __init__(self, response):
        super().__init__()

        self.code = response.status_code
        self.resp_mssg = response.reason

        self.tip = self._tip_library.get(self.code, self._default_tip)

        self.message = (
            f'Received response \n "[{self.code}] {self.resp_mssg}"\n---\n'
            f'Have you tried {self.tip}'
        )


# --------------------------------------------------------------------------
# Controller
# --------------------------------------------------------------------------


class Controller(App):

    CSS_PATH = ["papermate.tcss", "papermate_reqd.tcss"]

    BINDINGS = [
        Binding(key='q', action='quit', description='Quit'),
    ]

    def __init__(self, initial_view: str | type[ContentWindow] = 'base',
                 *initial_args) -> None:

        super().__init__()

        if isinstance(initial_view, str):
            match initial_view.casefold():
                case 'base':
                    initial_view = BaseView
                case 'daily':
                    initial_view = ListView
                case 'library':
                    initial_view = LibraryView

        self._start_view_mssg = ChangeView(initial_view, *initial_args)

        self._view_history = []

    async def on_change_view(self, message: ChangeView):
        # TODO I think this needs to put up a loading screen actually

        # self.loading = True

        self._view_history.append(message)

        new_view = message.to_view(*(message.view_args or []))

        try:
            self.query(ContentWindow).remove()
        except NoMatches:
            pass

        await self.mount(new_view)

        if new_view.can_focus:
            new_view.focus()

        # self.loading = False

    # TODO theres definitely a better way to do this
    async def on_previous_view(self, message: ChangeView):
        await self.on_change_view(self._view_history[-2])

    def on_cache_results(self, message: CacheResults):
        CACHE.cache_results(message.date, message.query_results)

    def compose(self) -> ComposeResult:

        yield TripleHeader()  # use set_title

        yield SplashScreen()  # TODO

        yield widgets.Footer()

    # TODO feel like there's a better way to do this...
    @on(ScreenReady)
    def _start_initial_view(self, event):
        self.post_message(self._start_view_mssg)
