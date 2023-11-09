#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.checkjob import submit_checks, submit_check_slot
from helpers.cluster import get_cluster, get_default_partition
from helpers.containerwrapper import create_containerwrapper
from helpers.setup_logging import setup_logging
from helpers.simconfig import SimConfig
from helpers.slurm import submit, SlurmConfig
from helpers.modules import find_powheg_releases, get_OSVersion
from helpers.workdir import find_index_of_input_file_range

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(simconfig: SimConfig, batchconfig: SlurmConfig) -> int:
    logging.info("Submitting POWHEG release %s", simconfig.powhegversion)
    logdir = os.path.join(simconfig.workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfilebase = "" 
    jobname = f"scalevar_{simconfig.powhegversion}"
    if batchconfig.njobs> 1:
        logfilebase = "joboutput_scale_%a.log"
    else: 
        logfilebase = f"joboutput_scale_{simconfig.minslot}.log"
        jobname += f"_{simconfig.minslot}"
    logfile = os.path.join(logdir,logfilebase)
    executable = os.path.join(repo, "run_powheg_singularity_scale.sh")
    runcmd = f"{executable} {batchconfig.cluster} {repo} {simconfig.workdir} {simconfig.process} {simconfig.powhegversion} {simconfig.powheginput} {simconfig.minslot}"
    if batchconfig.cluster == "CADES" or batchconfig.cluster == "CORI":
        runcmd = create_containerwrapper(runcmd, simconfig.workdir, batchconfig.cluster, get_OSVersion(batchconfig.cluster, simconfig.powhegversion))
    return submit(runcmd, batchconfig.cluster, jobname, logfile, get_default_partition(batchconfig.cluster) if batchconfig.partition == "default" else partition, batchconfig.njobs, f"{batchconfig.hours}:00:00", f"{batchconfig.memory}G", dependency=batchconfig.dependency)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="r3898", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--process", metavar="PROCESS", type=str, default="dijet", help="Process (default: dijet)")
    parser.add_argument("--slot", metavar="SLOT", type=int, default=-1, help="Process single slot (default: -1 := off)")
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
    minslot = 0
    njobs = 0
    if args.slot > -1:
        logging.info("Single job submission for slot %d", args.slot)
        minslot = args.slot 
        njobs = 1
    else:
        logging.info("Parallel mode: find jobs to run scaling on")
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

    simconfig = SimConfig()
    simconfig.workdir = args.workdir
    simconfig.powheginput = args.input
    simconfig.powhegversion = args.version
    simconfig.scalereweight = True
    simconfig.minslot = minslot
    simconfig.process = args.process

    batchconfig = SlurmConfig()
    batchconfig.cluster = cluster
    batchconfig.partition = partition
    batchconfig.njobs = njobs
    batchconfig.dependency = args.dependency
    batchconfig.hours = args.hours
    batchconfig.memory = args.mem

    logging.info("Simulating with POWHEG: %s", args.version)
    pwhgjob = submit_job(simconfig, batchconfig)
    logging.info("Job ID: %d", pwhgjob)

    if args.slot == -1:
        # submit checking job
        # must run as extra job, not guarenteed that the production job finished
        # only in parallel mode
        submit_checks(cluster, repo, args.workdir, args.partition, pwhgjob)
    else:
        # submit single checking job on missing slot
        # slot mode
        submit_check_slot(cluster, repo, args.workdir, args.slot, args.partition, pwhgjob)
