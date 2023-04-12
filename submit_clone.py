#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging
from helpers.slurm import submit

def submit_clone(inputdir: str, outputdir: str, partition: str):
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    executable = os.path.join(repo, "clone_workdir.sh")
    cmd = f"{executable} {inputdir} {outputdir}"
    logfile = os.path.join(os.path.dirname(outputdir), "workdir_clone.log")
    jobname = "workdir_clone"
    jobid = submit(cmd, get_cluster(), jobname, logfile, get_default_partition(get_cluster()) if partition == "default" else partition, 0, "04:00:00", "2G")
    logging.info("submitted clone job under ID %d", jobid)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_clone.py")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory")
    parser.add_argument("outputdir", metavar="OUTPUTDIR", type=str, help="Output directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="partition")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    submit_clone(os.path.abspath(args.inputdir), os.path.abspath(args.outputdir), args.partition)