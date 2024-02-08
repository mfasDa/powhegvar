#! /usr/bin/env python3

import argparse
import logging
import os

from helpers.setup_logging import setup_logging
from helpers.workarchive import pack_workarchives 

if __name__ == "__main__":
    parser = argparse.ArgumentParser("pack_workarchives_production.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-t", "--test", action="store_true", help="Test mode (only displays which directories to pack)")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean workdir")
    args = parser.parse_args()

    setup_logging(args.debug)
    wordkdir = os.path.abspath(args.workdir)
    chunks = sorted([x for x in os.listdir(wordkdir) if x.isdigit()])
    for dir in chunks:
        fullpath = os.path.join(wordkdir, dir)
        logging.info("Building grid archive in directory: %s", fullpath)
        if not args.test:
            pack_workarchives(fullpath, clean=args.clean)
