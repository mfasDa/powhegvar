#! /usr/bin/env python3

import argparse
import os

from helpers.setup_logging import setup_logging
from helpers.workarchive import pack_workarchives

if __name__ == "__main__":
    parser = argparse.ArgumentParser("build_workarchives.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory") 
    parser.add_argument("-c", "--clean", action="store_true", help="Clean workdir")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    workdir = os.path.abspath(args.workdir)
    pack_workarchives(workdir, args.clean)