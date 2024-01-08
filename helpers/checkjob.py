#! /usr/bin/env python3

import os
import logging
from helpers.cluster import get_default_partition
from helpers.slurm import submit 
from helpers.workdir import range_jobdirs

def submit_check_job(cluster: str, repo: str, workdir: str, partition: str,  mem: int = 2, hours: int = 4, dependency: list = []) -> int:
    runcmd = f"{repo}/run_check_pwgevents_single.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_check.log")
    jobname = "check_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_multi_checkjob(cluster: str, repo: str, workdir: str, partition: str, njobs: int, minslot: int = 0, mem: int = 2, hours: int = 1, dependency: list = []) -> int:
    runcmd = f"{repo}/run_check_pwgevents.sh {repo} {workdir} {minslot}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_check_%a.log")
    jobname = "check_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, njobs, f"{hours}:00:00", f"{mem}G", dependency)

def submit_check_jobs(cluster: str, repo: str, workdir: str, partition: str, mem: int = 2, hours: int =1, dependency: list = []) -> int:
    indexmin, indexmax = range_jobdirs(workdir)
    logging.debug(f"Min. index: {indexmin}, max index: {indexmax}")
    if indexmin == -1 or indexmax == -1:
        logging.error("Didn't find slot dirs in %s", workdir)
        return
    minslot = indexmin
    njobs = indexmax - indexmin + 1
    return submit_multi_checkjob(cluster, repo, workdir, partition, njobs, minslot, mem, hours, dependency)

def submit_check_job_slot(cluster: str, repo: str, workdir: str, slotID: int, partition: str, mem: int = 2, hours: int = 4, dependency: list = []) -> int:
    slotdir = os.path.join(workdir, "%04d" %slotID)
    runcmd = f"{repo}/run_check_pwgevents_slot.sh {repo} {slotdir} "
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, f"joboutput_check_{slotID}.log")
    jobname = f"check_pwgevents_{slotID}"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_check_summary(cluster: str, repo: str, workdir: str, partition: str,  mem: int = 2, hours: int = 4, dependency: list = []) -> int:
    runcmd = f"{repo}/run_checksummay_pwgevents.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_checksummary.log")
    jobname = "checksummary_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_checks(cluster: str, repo: str, workdir: str, partition: str, pwhgjob: list, multi: bool = False, summaryOnly: bool = False):
    checkjob = []
    if not summaryOnly:
        logging.info("Launching checking chain for workdir %s (%s-job mode)", workdir, "multi" if multi else "single")
        if multi:
            checkjob.append(submit_check_jobs(cluster, repo, workdir, partition, 2, 4, pwhgjob))
        else:
            checkjob.append(submit_check_job(cluster, repo, workdir, partition, 2, 4, pwhgjob))
        checkjobstring = ""
        for jobID in checkjob:
            if len(checkjobstring):
                checkjobstring += ", "
            checkjobstring += f"{jobID}"
        logging.info("Job ID(s) for automatic checking: %s", checkjobstring)
    else:
        logging.info("launching only final summary job")
    checksummaryjob = submit_check_summary(cluster, repo, workdir, partition, 2, 1, checkjob)
    logging.info("Job ID for analysing checking results: %d", checksummaryjob)

def submit_check_slot(cluster: str, repo: str, workdir: str, slot: int, partition: str, pwhgjob: int) -> int:
    slotworkdir = os.path.join(workdir, "%04d" %slot)
    logging.info("Submitting single check job for workdir: %s", slotworkdir)
    checkjob = submit_check_job_slot(cluster, repo, workdir, slot, partition, 2, 4, [pwhgjob])
    return checkjob