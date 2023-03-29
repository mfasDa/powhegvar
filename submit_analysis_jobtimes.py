#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.cluster import get_cluster, get_default_partition
from helpers.slurm import submit

def submit_analysis_job(workdir: str, pattern: str, outputfile: str, tag: str="") -> int:
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    executable = os.path.join(repo, "run_analysis_jobtimes.sh")
    runcmd = f"{executable} {repo} {workdir} {pattern} {outputfile}"
    if len(tag):
        runcmd += f" \"{tag}\""
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "analysis_jobtimes.log")
    return submit(runcmd, get_cluster(), "analysis_jobtimes", logfile, get_default_partition(get_cluster()), 0, "02:00:00", "2G")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_analysis_jobtimes.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("pattern", metavar="PATTERN", type=str, help="Log file pattern")
    parser.add_argument("outputfile", metavar="OUTPUTFILE", type=str, help="Output file inside workdir")
    parser.add_argument("-t", "--tag", metavar="TAG", type=str, default="", help="Tag (optional)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    jobid = submit_analysis_job(args.workdir, args.pattern, args.outputfile, args.tag)
    logging.info("Submitted analysis job under ID %d", jobid)