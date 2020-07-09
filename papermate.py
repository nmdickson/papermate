import feedparser

import curses as cs

import interface


if __name__ == '__main__':
    cs.wrapper(interface.Interface().mainloop)

    url = f"http://export.arxiv.org/api/query?search_query=cat:astro-ph&max_results=1&sortBy=submittedDate"

    entries = feedparser.parse(url).entries
