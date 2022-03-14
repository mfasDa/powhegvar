#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.cluster import get_cluster, get_default_partition
from helpers.slurm import submit

repo = os.path.abspath(os.path.dirname(sys.argv[0]))

def build_logfile(logfile: str):
    logdir = os.path.dirname(logfile)
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    return logfile

def submit_split(cluster: str, outputbase: str, rootfile: str, partition: str, dependency: int):
    script = os.path.join(repo, "split_steer.sh")
    command = "{} {} {} {} {}".format(script, cluster, repo, outputbase, rootfile)
    logfile = build_logfile(os.path.join(outputbase, "logs", "split.log"))
    return submit(command, cluster, "split_root", logfile, partition, 0, "03:00:00", "4G", dependency) 

def do_submit_split(inputdir: str, rootfile: str):
    cluster = get_cluster()
    splitjob = submit_split(cluster, inputdir, rootfile, get_default_partition(cluster), -1)
    logging.info("Submitted merging job under ID %d", splitjob)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_merge.py", description="Submitter for merging")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory with POWHEG chunks")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default="Pythia8JetSpectra.root", help="ROOT file to be merged")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    do_submit_split(os.path.abspath(args.inputdir), args.file)