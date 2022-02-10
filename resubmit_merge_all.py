#! /usr/bin/env python3

import argparse
import logging
import os
from submit_merge import do_submit_merge
from helpers.setup_logging import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_merge.py", description="Submitter for merging")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory with POWHEG chunks")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default="Pythia8JetSpectra.root", help="ROOT file to be merged")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    inputdir = os.path.abspath(args.inputdir)
    for dr in os.listdir(inputdir):
        pydir = os.path.join(inputdir, dr)
        if os.path.isdir(pydir):
            logging.info("Submitting merge for %s", pydir)
            do_submit_merge(pydir, args.file)