import curses as cs
import logging
import textwrap as tw


def draw_listview(window, articles):
    window.clear()

    height, width = window.getmaxyx()

    for ind, article in enumerate(articles):

        # TODO the y depends on text wrapping, figure it out
        x, y = 10, 2 + ind * 10

        marker = f'[{ind}] '

        window.addstr(y, x, marker)

        x += len(marker)

        # TODO et al. or all authors should be in options
        authors = article.authors[0] + ' et al.'
        short_abstract = tw.shorten(article.abstract, 400, placeholder='...')

        window.addstr(y, x, article.title, cs.A_BOLD)
        window.addstr(y + 1, x, authors, cs.A_DIM)

        abs_win = window.derwin(6, width - 30, y + 2, x)
        abs_win.addstr(0, 0, short_abstract)

    window.refresh()


def draw_detailedview(window, article):
    '''draw the detailed "more" page for a chosen article'''
    window.clear()

    x, y = 10, 2
    max_height, max_width = window.getmaxyx()
    width = max_width - 2 * x

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
