import curses as cs
import logging


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

        window.addstr(y, x, article.title, cs.A_BOLD)
        window.addstr(y + 1, x, article.authors[0] + ' et al.', cs.A_DIM)

        # TODO use textwrapper module as well, to avoid splitting words
        abs_win = window.derwin(6, width - 30, y + 2, x)
        abs_win.addstr(0, 0, article.abstract[:400] + '...')

    window.refresh()


def draw_detailedview(window, article):
    '''draw the detailed "more" page for a chosen article'''
    window.clear()

    height, width = window.getmaxyx()

    x, y = 5, 2

    title_win = window.derwin(2, width - 30, y, x)
    title_win.addstr(0, 0, article.title, cs.A_BOLD)

    auth_win = window.derwin(4, width - 30, y + 3, x + 5)
    auth_win.addstr(0, 0, ', '.join(article.authors), cs.A_DIM)

    abs_win = window.derwin(height - 10, width - 30, y + 7, x + 5)
    abs_win.addstr(0, 0, article.abstract)

    window.refresh()
