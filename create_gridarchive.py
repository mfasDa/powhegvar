#! /usr/bin/env python3

import argparse
import logging

from helpers.gridarchive import build_archive
from helpers.setup_logging import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser("create_gridarchive.py")
    parser.add_argument("griddir", metavar="GRIDDIR", type=str, help="Directory with gridfiles")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean grid files after archive creation")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    logging.info("Creating grid archive in directory: %s", args.griddir)
    build_archive(args.griddir, args.force, args.clean)
