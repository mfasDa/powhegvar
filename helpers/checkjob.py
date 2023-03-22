#! /usr/bin/env python3

import os
import logging
from helpers.cluster import get_default_partition
from helpers.slurm import submit 

def submit_check_job(cluster: str, repo: str, workdir: str, partition: str,  mem: int = 2, hours: int = 4, dependency: int = -1) -> int:
    runcmd = f"{repo}/run_check_pwgevents_single.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_check.log")
    jobname = "check_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_check_summary(cluster: str, repo: str, workdir: str, partition: str,  mem: int = 2, hours: int = 4, dependency: int = -1) -> int:
    runcmd = f"{repo}/run_checksummay_pwgevents.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_checksummary.log")
    jobname = "checksummary_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_checks(cluster: str, repo: str, workdir: str, partition: str, pwhgjob):
    logging.info("Launching checking chain for workdir %s", workdir)
    checkjob = submit_check_job(cluster, repo, workdir, partition, 2, 4, pwhgjob)
    logging.info("Job ID for automatic checking: %d", checkjob)
    checksummaryjob = submit_check_summary(cluster, repo, workdir, partition, 2, 1, checkjob)
    logging.info("Job ID for analysing checking results: %d", checksummaryjob)