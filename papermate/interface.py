import curses as cs


def draw_listview(window, articles):
    window.clear()

    window.border()

    height, width = window.getmaxyx()

    for ind, article in enumerate(articles):

        # TODO the 5 depends on text wrapping, figure it out
        x, y = 3, 2 + ind * 10

        marker = f'[{ind}] '

        window.addstr(y, x, marker)

        x += len(marker)

        # TODO et al. or all authors should be in options

        window.addstr(y, x, article.title, cs.A_BOLD)
        window.addstr(y + 1, x, article.authors[0] + ' et al.', cs.A_DIM)

        # TODO use textwrapper as well, to avoid splitting words
        abs_win = window.subwin(6, width - 20, y + 3, x)
        abs_win.addstr(0, 0, article.abstract[:400] + '...')


def draw_detailedview(window, article):
    '''draw the detailed "more" page for a chosen article'''
    window.clear()
    pass
