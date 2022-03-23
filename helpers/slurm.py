#! /usr/bin/env python3

import logging
import subprocess

def ncorejob(cluster: str, cpus: int, jobname: str, logfile: str, partition: str, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> str:
    logging.info("Using logfile: %s", logfile)
    submitcmd = "sbatch "
    if cluster == "CADES":
        submitcmd += " -A birthright" 
    submitcmd += " -N 1 -n 1 -c {}".format(cpus)
    if cluster == "CORI":
        submitcmd += " --qos={}".format(partition)
    else:
        submitcmd += " --partition {}".format(partition)
    submitcmd += " -J {}".format(jobname)
    submitcmd += " -o {}".format(logfile)
    if cluster == "CADES" or cluster == "CORI":
        submitcmd += " --time={}".format(timelimit)
        submitcmd += " --mem={}".format(memory)
    if dependency > -1:
        submitcmd += " -d {}".format(dependency)
    if cluster == "CORI":
        submitcmd += " --constraint=haswell"
        submitcmd += " --licenses=cvmfs,cfs"
        submitcmd += " --image=docker:mfasel/cc7-alice:latest"
    return submitcmd


def submit(command: str, cluster: str, jobname: str, logfile: str, partition: str, arraysize: int = 0, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> int:
    submitcmd = ncorejob(cluster, 1, jobname, logfile, partition, timelimit, memory, dependency)
    if arraysize > 0:
        submitcmd += " --array=0-{}".format(arraysize-1)
    submitcmd += " {}".format(command)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid

def submit_range(command: str, cluster: str, jobname: str, logfile: str, partition: str, arrayrange: dict, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> int:
    submitcmd = ncorejob(cluster, 1, jobname, logfile, partition, timelimit, memory, dependency)
    submitcmd += " --array={}-{}".format(arrayrange["first"], arrayrange["last"])
    submitcmd += " {}".format(command)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid