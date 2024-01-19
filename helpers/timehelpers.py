#! /usr/bin/env python3

import logging

def log_elapsed_time(tag: str, starttime: float, endtime: float):
    elapsed_seconds = endtime - starttime
    hours = elapsed_seconds / 3600
    minutes = (elapsed_seconds / 60) % 60
    seconds = elapsed_seconds % 60
    logging.info("%s finished, took %d:%d:%d (%d seconds total)", tag, hours, minutes, seconds, elapsed_seconds)