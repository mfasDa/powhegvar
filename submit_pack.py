#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.cluster import get_cluster, get_default_partition
from helpers.slurm import submit
from helpers.setup_logging import setup_logging

def submit_pack(workdir: str, cluster: str, partition: str):
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    logfile = os.path.join(workdir, "logs", "pack.log")
    jobname = "pack_pwgresults"
    cmd = f"{repo}/pack_workdir.py -b {workdir}"
    jobid = submit(cmd, cluster, jobname, logfile, get_default_partition(cluster) if partition=="default" else partition, 0, "05:00:00", "2G")
    logging.info("Submitting pack job under jobid %d", jobid)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_pack.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="working directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    submit_pack(os.path.abspath(args.workdir), get_cluster(), args.partition)