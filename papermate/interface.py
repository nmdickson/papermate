import curses as cs
import textwrap as tw


def draw_listview(window, articles):
    # TODO et al. or all authors should be in options
    window.clear()

    y = 0
    max_height, max_width = window.getmaxyx()

    for ind, article in enumerate(articles):

        # TODO the y depends on text wrapping, figure it out
        width = max_width - 25
        x = 10
        y += 2

        # ----------------------------------------------------------------------
        # Numeric label
        # ----------------------------------------------------------------------

        marker = f'[{ind}] '
        window.addstr(y, x, marker)
        x += len(marker)
        width -= len(marker)

        # ----------------------------------------------------------------------
        # Title
        # ----------------------------------------------------------------------

        title = tw.wrap(article.title, width)

        title_win = window.derwin(len(title), width, y, x)

        for ind, line in enumerate(title):
            title_win.addstr(ind, 0, line, cs.A_BOLD)

        # ----------------------------------------------------------------------
        # Author
        # ----------------------------------------------------------------------

        y += len(title)

        authors = tw.wrap(article.authors[0] + ' et al.', width)

        auth_win = window.derwin(len(authors), width, y, x)

        for ind, line in enumerate(authors):
            auth_win.addstr(ind, 0, line, cs.A_DIM)

        # ----------------------------------------------------------------------
        # Abstract
        # ----------------------------------------------------------------------

        y += len(authors)

        short_abstract = tw.shorten(article.abstract, 400, placeholder='...')
        short_abstract = tw.wrap(short_abstract, width)

        abs_win = window.derwin(len(short_abstract), width, y, x)

        for ind, line in enumerate(short_abstract):
            abs_win.addstr(ind, 0, line)

        y += len(short_abstract)

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

    # ----------------------------------------------------------------------
    # Abstract
    # ----------------------------------------------------------------------

    y += len(authors) + 1

    abstract = tw.wrap(article.abstract, width)

    abs_win = window.derwin(len(abstract), width, y, x)

    for ind, line in enumerate(abstract):
        abs_win.addstr(ind, 0, line)

    window.refresh()
