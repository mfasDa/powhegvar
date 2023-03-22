#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging
from helpers.slurm import submit

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(cluster: str, workdir: str, partition: str, njobs: int, minslot: int = 0, mem: int = 2, hours: int = 1) -> int:
    runcmd = f"{repo}/run_check_pwgevents.sh {repo} {workdir} {minslot}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_check_%a.log")
    jobname = "check_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, njobs, f"{hours}:00:00", f"{mem}G")

def range_jobdirs(workdir: str) -> tuple:
    jobdirs = sorted([x for x in os.listdir(workdir) if os.path.isdir(os.path.join(workdir, x)) and x.isdigit()])
    if not len(jobdirs):
        return (-1, -1)
    return (int(jobdirs[0]), int(jobdirs[len(jobdirs) -1]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_check_pwgevents.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    if not os.path.exists(args.workdir):
        logging.error("Working directory %s doesn't exist", args.workdir)
        sys.exit(1)
    indexmin, indexmax = range_jobdirs(args.workdir)
    logging.debug(f"Min. index: {indexmin}, max index: {indexmax}")
    if indexmin == -1 or indexmax == -1:
        logging.error("Didn't find slot dirs in %s", args.workdir)
        sys.exit(1)
    minslot = indexmin
    njobs = indexmax - indexmin + 1
    
    checkjob = submit_job(cluster, args.workdir, args.partition, njobs, minslot, args.mem, args.hours)
    logging.info("Job ID: %d", checkjob)