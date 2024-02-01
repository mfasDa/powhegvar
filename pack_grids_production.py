#! /usr/bin/env python3

import argparse
import logging
import os

from helpers.gridarchive import build_archive
from helpers.setup_logging import setup_logging

def find_unpacked_chunks(basedir: str, gridarchive: str) -> list:
    unpacked = []
    for dir in os.listdir(basedir):
        if not dir.isdigit():
            continue
        testarchive = os.path.join(basedir, dir, gridarchive)
        if not os.path.exists(testarchive):
            unpacked.append(dir)
    return sorted(unpacked)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("pack_grids_production.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-g", "--gridarchive", metavar="FILE", type=str, default="grids.zip", help="Name of the grid archive file")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-t", "--test", action="store_true", help="Test mode (only displays which directories to pack)")
    args = parser.parse_args()

    setup_logging(args.debug)
    wordkdir = os.path.abspath(args.workdir)
    nonpacked = find_unpacked_chunks(wordkdir, args.gridarchive)
    for dir in nonpacked:
        fullpath = os.path.join(wordkdir, dir)
        logging.info("Building grid archive in directory: %s", fullpath)
        if not args.test:
            build_archive(fullpath, force_overwrite=False, clean=True)
