#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.checkjob import submit_checks
from helpers.cluster import get_cluster, get_default_partition
from helpers.containerwrapper import create_containerwrapper
from helpers.datahandler import find_pwgevents
from helpers.powheg import is_valid_process
from helpers.powhegconfig import get_energy_from_config
from helpers.setup_logging import setup_logging
from helpers.slurm import submit_range, SlurmConfig
from helpers.modules import find_powheg_releases, get_OSVersion
from helpers.simconfig import SimConfig

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(simconfig: SimConfig, batchconfig: SlurmConfig, singleslot: bool = False):
    logging.info("Submitting POWHEG release %s", simconfig.powhegversion)
    powheg_version_string = simconfig.powhegversion
    if "VO_ALICE@POWHEG::" in powheg_version_string:
        powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
    workdir= os.path.join(simconfig.workdir, f"POWHEG_{powheg_version_string}")
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = ""
    if singleslot:
        logfile = os.path.join(logdir, f"joboutput{simconfig.minslot}.log")
    else:
        logfile = os.path.join(logdir, "joboutput%a.log")
    executable = os.path.join(repo, "run_powheg_singularity.sh")
    energytag = "%.1fT" %(get_energy_from_config(simconfig.powheginput)/1000)
    logging.info("Running simulation for energy %s", energytag)
    runcmd = f"{executable} {batchconfig.cluster} {repo} {workdir} {simconfig.process} {simconfig.powhegversion} {simconfig.powheginput} {simconfig.minslot} {simconfig.gridrepository} {simconfig.nevents}"
    jobname = f"pp_{simconfig.process}_{energytag}"
    if batchconfig.cluster == "CADES" or batchconfig.cluster == "PERLMUTTER":
        runcmd = create_containerwrapper(runcmd, workdir, batchconfig.cluster, get_OSVersion(batchconfig.cluster, simconfig.powhegversion))
    elif batchconfig.cluster == "B587" and "VO_ALICE" in simconfig.powhegversion:
        # needs container also on the 587 cluster for POWHEG versions from cvmfs
        # will use the container from ALICE, so the OS version does not really matter
        runcmd = create_containerwrapper(runcmd, workdir, batchconfig.cluster, "CentOS8")
    logging.debug("Running on hosts: %s", runcmd)
    return submit_range(runcmd, batchconfig.cluster, jobname, logfile, get_default_partition(batchconfig.cluster) if batchconfig.partition == "default" else batchconfig.partition, {"first": 0, "last": batchconfig.njobs-1}, "{}:00:00".format(batchconfig.hours), "{}G".format(batchconfig.memory))

def build_workdir_for_pwhg(workdir: str, powheg_version: str) -> str:
    powheg_version_string = powheg_version
    if "VO_ALICE@POWHEG::" in powheg_version_string:
        powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
    return os.path.join(workdir, f"POWHEG_{powheg_version_string}") 

def prepare_outputlocation(outputlocation: str):
    if not os.path.exists(outputlocation):
        os.makedirs(outputlocation, 0o755)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=0, help="Number of events (default: 0:=Default number of events in powheg.input)")
    parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=200, help="Number of slots")
    parser.add_argument("-m", "--minslot", metavar="MINSLOT", type=int, default=0, help="Min. slot ID")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="all", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-g", "--grids", metavar="GRIDS", type=str, default="NONE", help="Old grids (default: NONE")
    parser.add_argument("--process", metavar="PROCESS", type=str, default="dijet", help="Process (default: dijet)")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
  
    cluster = get_cluster()
    if cluster == None:
        logging.error("Failed to detect computing cluster")
        sys.exit(1)
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    if not is_valid_process(args.process):
        logging.error("Process \"%s\" not valid", args.process)
        sys.exit(1)

    simconfig = SimConfig()
    simconfig.workdir = args.workdir
    simconfig.gridrepository = args.grids
    simconfig.nevents = args.events
    simconfig.powheginput = args.input
    simconfig.minslot = args.minslot
    simconfig.process = args.process

    batchconfig = SlurmConfig()
    batchconfig.cluster = cluster
    batchconfig.partition = partition
    batchconfig.njobs = args.njobs
    batchconfig.memory = args.mem
    batchconfig.hours = args.hours

    prepare_outputlocation(args.workdir)	
    # check if the output location has already POWHEG_events
    pwgevents = find_pwgevents(args.workdir)
    if len(pwgevents):
        logging.error("Working directory not empty, output would be overwritten")
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
        simconfig.powhegversion = pwhg
        pwhgjob = submit_job(simconfig, batchconfig)
        logging.info("Job ID for POWHEG %s: %d", pwhg, pwhgjob)

        # submit checking job
        # must run as extra job, not guarenteed that the production job finished
        submit_checks(cluster, repo, build_workdir_for_pwhg(args.workdir, pwhg), args.partition, [pwhgjob]) 
	
