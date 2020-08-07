import curses as cs

def draw_listview(self, window, articles):

    for ind, article in enumerate(articles):

        # TODO the 5 depends on text wrapping, figure it out
        x, y = 3, ind * 5

        marker = f'[{ind}] '

        window.addstr(y, x, marker)

        x += len(marker)

        # TODO et al. or all authors should be in options
        # TODO make sure abstract wraps correctly

        window.addstr(y, x, article.title, cs.A_BOLD)
        window.addstr(y + 1, x, article.authors[0] + ' et al.', cs.A_DIM)
        window.addstr(y + 3, x, article.abstract[:400] + '...')


def draw_detailedview(self, window, article):
    '''draw the detailed "more" page for a chosen article'''
    pass
