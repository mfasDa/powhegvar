#! /usr/bin/env python3

import argparse
import logging
import os

from helpers.setup_logging import setup_logging
from helpers.gridarchive import gridarchive

if __name__ == "__main__":
    cwd = os.path.abspath(os.getcwd())
    parser = argparse.ArgumentParser()
    parser.add_argument("gridarchive", metavar="GRDIARCHIVE", type=str, help="Archive file with grids")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, default=cwd, help="Directory where grids should be installed (default: current directory)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    archive = gridarchive()
    if args.outputdir != cwd:
        if not os.path.exists(args.outputdir):
            os.makedirs(args.outputdir, 0o755)
        os.chdir(args.outputdir)
    archive.extract(args.gridarchive)
    if not archive.check():
        logging.error("Grid archive %s incomplete", args.gridarchive)
    else:
        logging.info("Grid archive consistent")
    archive.list()
    os.chdir(cwd)