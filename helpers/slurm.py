#! /usr/bin/env python3

import logging
import subprocess

def submit(command: str, jobname: str, logfile: str, partition: str, arraysize: int = 0, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> int:
    logging.info("Using logfile: %s", logfile)
    submitcmd = "sbatch -A birthright -N 1 -n 1 -c 1"
    submitcmd += " --partition {}".format(partition)
    submitcmd += " -J {}".format(jobname)
    submitcmd += " -o {}".format(logfile)
    submitcmd += " --time={}".format(timelimit)
    submitcmd += " --mem={}".format(memory)
    if arraysize > 0:
        submitcmd += " --array=0-{}".format(arraysize-1)
    if dependency > -1:
        submitcmd += " -d {}".format(dependency)
    submitcmd += " {}".format(command)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid

def submit_range(command: str, jobname: str, logfile: str, partition: str, arrayrange: dict, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> int:
    logging.info("Using logfile: %s", logfile)
    submitcmd = "sbatch -A birthright -N 1 -n 1 -c 1"
    submitcmd += " --partition {}".format(partition)
    submitcmd += " -J {}".format(jobname)
    submitcmd += " -o {}".format(logfile)
    submitcmd += " --time={}".format(timelimit)
    submitcmd += " --mem={}".format(memory)
    submitcmd += " --array={}-{}".format(arrayrange["first"], arrayrange["last"])
    if dependency > -1:
        submitcmd += " -d {}".format(dependency)
    submitcmd += " {}".format(command)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid