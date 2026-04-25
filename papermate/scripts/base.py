#!/usr/bin/env python3

import papermate
from papermate.interface import ChangeView, BaseView, ListView, LibraryView

import datetime


# TODO support old way as option ?? Unlikely tbh
# import curses as cs
# def main():
#     cs.wrapper(papermate.controller)
# def daily():
#     cs.wrapper(papermate.controller, mode='daily')
# def library():
#     cs.wrapper(papermate.controller, mode='library')


def start_app(initial_view=BaseView, *args):

    print("STARTING APP")

    app = papermate.Controller(initial_view, *args)
    app.run()


def main():
    start_app(BaseView)


def daily():
    date = datetime.datetime.today()
    start_app(ListView, [date, ])


# def library():  # TODO
#     start_app(LibraryView)

if __name__ == '__main__':
    main()
    # daily()