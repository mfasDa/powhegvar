#! /usr/bin/env python3

import argparse
import logging
import os
from submit_pythia import submit_merge
from helpers.setup_logging import setup_logging
from helpers.cluster import get_cluster, get_default_partition

def do_submit_merge(inputdir: str, rootfile: str = "Pythia8JetSpectra.root"):
    cluster = get_cluster()
    mergejob = submit_merge(cluster, inputdir, rootfile, get_default_partition(cluster), -1)
    logging.info("Submitted merging job under ID %d", mergejob)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_merge.py", description="Submitter for merging")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory with POWHEG chunks")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default="Pythia8JetSpectra.root", help="ROOT file to be merged")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    do_submit_merge(os.path.abspath(args.inputdir), args.file)