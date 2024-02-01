#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.cluster import get_cluster, get_fast_partition
from helpers.slurm import submit

if __name__ == "__main__":
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    parser = argparse.ArgumentParser("submit_repack_grids.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-g", "--gridarchive", metavar="GRIDARCHIVE", type=str, default="grids.zip", help="Name of the grid archive")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-t", "--test", action="store_true", help="Test mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    cluster = get_cluster()
    if not cluster:
        logging.error("Cluster could not be determined")
        sys.exit(1)

    workdir = os.path.abspath(args.workdir)
    executable = os.path.join(repo, "repack_grids_runner.sh")
    cmd=f"{executable} {repo} {workdir} {args.gridarchive}"
    logging.info("Launing: %s", cmd)
    if not args.test:
        logfile = os.path.join(workdir, "logs", "gridsrepack.log")
        jobid = submit(cmd, cluster, "repack_grids", logfile, get_fast_partition(cluster))
        logging.info("Submitted pack job under job ID %d", jobid)