#!/usr/bin/env python3

import papermate
import curses as cs

import logging

logging.basicConfig(filename='pmate.log', filemode='w', level=logging.DEBUG)


def main():
    cs.wrapper(papermate.controller)


def daily():
    cs.wrapper(papermate.controller, mode='daily')


def library():
    cs.wrapper(papermate.controller, mode='library')
