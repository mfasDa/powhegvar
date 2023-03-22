#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging
from helpers.slurm import submit
from helpers.modules import find_powheg_releases

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(cluster: str, workdir: str, powheg_version: str, powheg_input: str, partition: str, njobs: int, minslot: int = 0, mem: int = 4, hours: int = 10, dependency: int = 0):
    print(f"Submitting POWHEG release {powheg_version}")
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, f"joboutput_scale_%a.log")
    executable = os.path.join(repo, "powheg_steer_scale.sh")
    runcmd = f"{executable} {cluster} {repo} {workdir} {powheg_version} {powheg_input} {minslot}"
    jobname = f"scalevar_{powheg_version}"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, njobs, f"{hours}:00:00", f"{mem}G", dependency=dependency)

def find_index_of_input_file_range(workdir: str) -> int:
    pwgdirs = sorted([int(x) for x in os.listdir(workdir) if os.path.isfile(os.path.join(workdir, x, "pwgevents.lhe"))])
    if not len(pwgdirs):
        return (-1, -1)
    return (pwgdirs[0], pwgdirs[len(pwgdirs)-1]) 


if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="r3898", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("--dependency", metavar="DEPENDENCY", type=int, default=-1, help="Dependency")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
  
    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    if not os.path.exists(args.workdir):
        logging.error("Working directory %s doesn't exist", args.workdir)
        sys.exit(1)
    indexmin, indexmax = find_index_of_input_file_range(args.workdir)
    logging.debug(f"Min. index: {indexmin}, max index: {indexmax}")
    if indexmin == -1 or indexmax == -1:
        logging.error("Didn't find slot dirs with pwgevents.lhe in %s", args.workdir)
        sys.exit(1)
    minslot = indexmin
    njobs = indexmax - indexmin + 1
    request_release = args.version
    if cluster == "CADES":
        releases_all = find_powheg_releases() if cluster == "CADES" else ["default"]
        if not request_release in releases_all:
            print("requested POWHEG not found: {}".format(args.version))
            sys.exit(1)
    else:
        if not "VO_ALICE" in request_release:
            request_release = "default"
    print("Simulating with POWHEG: {}".format(args.version))
    pwhgjob = submit_job(cluster, args.workdir, args.version, args.input, args.partition, njobs, minslot, args.mem, args.hours, args.dependency)
    logging.info("Job ID: %d", pwhgjob)
	
