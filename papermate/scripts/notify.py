#!/usr/bin/env python3

import papermate
from papermate.utils import CONFIG

import os
import logging
import warnings
import subprocess


logging.basicConfig(filename=CONFIG.log_file, filemode='w', level=logging.DEBUG)


def _notify_wall(notif, banner=False, timeout=None):
    '''Raise a notification using the `wall` command.'''

    # Don't let wall hang on an empty message
    if not notif:
        return

    cmd = ["wall"]

    if banner is False:
        if os.geteuid() == 0:
            cmd.append("-n")
        else:
            mssg = "--nobannner is available only for root"
            warnings.warn(mssg)

    if timeout is not None:
        cmd.extend(["-t", f"{timeout}"])

    cmd.append(notif)

    subprocess.run(cmd)


def _notify_alert():
    '''Raise a notification using the actual system alerts.'''
    raise NotImplementedError


def broadcast_reminder(method='wall', show_count=True):

    mssg = f"PAPERMATE REMINDER - "

    if show_count:
        res = papermate.queries.QuerySet.from_configfile(CONFIG).execute()
        count = len(res.articles)

        mssg += f"{count} new articles to read today!"

    else:

        mssg += "Read today's papers!"

    _notify_wall(notif=mssg, timeout=3600)
