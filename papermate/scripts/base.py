#!/usr/bin/env python3

import papermate
from papermate.utils import CONFIG

import logging
import curses as cs


logging.basicConfig(filename=CONFIG.log_file, filemode='w', level=logging.DEBUG)


def main():
    cs.wrapper(papermate.controller)


def daily():
    cs.wrapper(papermate.controller, mode='daily')


def library():
    cs.wrapper(papermate.controller, mode='library')
