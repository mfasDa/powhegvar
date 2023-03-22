#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.cluster import get_cluster, get_default_partition
from helpers.datahandler import find_pwgevents
from helpers.setup_logging import setup_logging
from helpers.slurm import submit, submit_range
from helpers.modules import find_powheg_releases

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(cluster: str, workdir: str, powheg_version: str, powheg_input: str, partition: str, njobs: int, minslot: int = 0, mem: int = 4, hours: int = 10, reweightmode: bool = False, reweightID: int = -1, oldgrids: str = "NONE"):
    print("Submitting POWHEG release {}".format(powheg_version))
    powheg_version_string = powheg_version
    if "VO_ALICE@POWHEG::" in powheg_version_string:
        powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
    logdir = os.path.join(workdir, f"POWHEG_{powheg_version_string}", "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput%a.log")
    executable = os.path.join(repo, "powheg_steer.sh")
    numreweightmode =  1 if reweightmode else 0
    runcmd = f"{executable} {cluster} {repo} {workdir} {powheg_version} {powheg_input} {minslot} {numreweightmode} {reweightID} {oldgrids}"
    jobname = f"pjj13T_{powheg_input}"
    return submit_range(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, {"first": 0, "last": njobs-1}, "{}:00:00".format(hours), "{}G".format(mem))

def submit_check_job(cluster: str, workdirbase: str, powheg_version: str, partition: str,  mem: int = 2, hours: int = 4, dependency: int = -1) -> int:
    powheg_version_string = powheg_version
    if "VO_ALICE@POWHEG::" in powheg_version_string:
        powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
    workdir = os.path.join(workdirbase, f"POWHEG_{powheg_version_string}") 
    runcmd = f"{repo}/run_check_pwgevents_single.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_check.log")
    jobname = "check_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)

def submit_check_summary(cluster: str, workdirbase: str, powheg_version: str, partition: str,  mem: int = 2, hours: int = 1, dependency: int = -1):
    powheg_version_string = powheg_version
    if "VO_ALICE@POWHEG::" in powheg_version_string:
        powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
    workdir = os.path.join(workdirbase, f"POWHEG_{powheg_version_string}") 
    runcmd = f"{repo}/run_checksummay_pwgevents.sh {repo} {workdir}"
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_checksummary.log")
    jobname = "checksummary_pwgevents"
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, 0, f"{hours}:00:00", f"{mem}G", dependency)
    pass

def prepare_outputlocation(outputlocation: str):
    if not os.path.exists(outputlocation):
        os.makedirs(outputlocation, 0o755)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=200, help="Number of slots")
    parser.add_argument("-m", "--minslot", metavar="MINSLOT", type=int, default=0, help="Min. slot ID")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="all", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-r", "--reweight", action="store_true", help="Reweight mode")
    parser.add_argument("-w", "--weightid", metavar="WEIGHTID", type=int, default=0, help="ID of the weight")
    parser.add_argument("-g", "--grids", metavar="GRIDS", type=str, default="NONE", help="Old grids (default: NONE")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
  
    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    prepare_outputlocation(args.workdir)	
    # check if the output location has already POWHEG_events
    pwgevents = find_pwgevents(args.workdir)
    if len(pwgevents):
        if not args.reweight:
            logging.error("Working directory not empty, output would be overwritten")
            sys.exit(1)
    elif args.reweight:
        logging.error("Reweighting mode requested on input directory without POWHEG input")
        sys.exit(1)

    releases = []
    release_all = find_powheg_releases() if cluster == "CADES" else ["default", "FromALICE"]
    if args.version == "all":
        releases = release_all
    else:
        if not args.version:
            print("requested POWHEG not found: {}".format(args.version))
            sys.exit(1)
        releases.append(args.version)
        print("Simulating with POWHEG: {}".format(releases))
    for pwhg in releases:
        pwhgjob = submit_job(cluster, args.workdir, pwhg, args.input, args.partition, args.njobs, args.minslot, args.mem, args.hours, oldgrids=args.grids)
        logging.info("Job ID for POWHEG %s: %d", pwhg, pwhgjob)

        # submit checking job
        # must run as extra job, not guarenteed that the production job finished
        checkjob = submit_check_job(cluster, args.workdir, pwhg, args.partition, 2, 4, pwhgjob)
        logging.info("Job ID for automatic checking: %d", checkjob)
        checksummaryjob = submit_check_summary(cluster, args.workdir, pwhg, args.partition, 2, 1, checkjob)
	
