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
from helpers.workdir import find_index_of_input_file_range

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def make_powhegrunner(config: SimConfig) -> str:
    executable = f"{repo}/powheg_runner.py"
    workdir = os.path.join(config.workdir, f"POWHEG_{config.powhegversion}")
    cmd = f"{executable} {workdir} -t {config.process}"
    if not config.is_scalereweight() and not config.is_pdfreweight():
        cmd += f" -i {config.powheginput}"
        if config.nevents > 0:
            cmd += f" -e {config.nevents}"
    if config.minslot > 0:
        cmd += f" --slotoffset {config.minslot}"
    if len(config.gridrepository) and config.gridrepository != "NONE":
        cmd += f" -g {config.gridrepository}"
    if config.is_scalereweight():
        cmd += " -s --minid 0"
    if config.is_pdfreweight():
        cmd += f" --minpdf {config.minpdf} --maxpdf {config.maxpdf} --minid {config.minID}"
    logging.debug("Running POWHEG command: %s", cmd)
    return cmd

def configure_env(cluster: str, powhegversion: str) -> str:
    executable = f"{repo}/powheg_run_in_env.sh"
    return f"{executable} {repo} {cluster} {powhegversion}"

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
    energytag = "%.1fT" %(get_energy_from_config(simconfig.powheginput)/1000) if simconfig.powheginput else "None"
    logging.info("Running simulation for energy %s", energytag)
    runcmd =  "%s %s" %(configure_env(batchconfig.cluster, simconfig.powhegversion), make_powhegrunner(simconfig))
    #executable = os.path.join(repo, "run_powheg_singularity.sh")
    #f"{executable} {batchconfig.cluster} {repo} {workdir} {simconfig.process} {simconfig.powhegversion} {simconfig.powheginput} {simconfig.minslot} {simconfig.gridrepository} {simconfig.nevents}"
    jobname = f"pp_{simconfig.process}_{energytag}"
    if batchconfig.cluster == "CADES" or batchconfig.cluster == "PERLMUTTER":
        runcmd = "%s %s" %(create_containerwrapper(workdir, batchconfig.cluster, get_OSVersion(batchconfig.cluster, simconfig.powhegversion)), runcmd)
    elif batchconfig.cluster == "B587" and "VO_ALICE" in simconfig.powhegversion:
        # needs container also on the 587 cluster for POWHEG versions from cvmfs
        # will use the container from ALICE, so the OS version does not really matter
        runcmd = "%s %s" %(create_containerwrapper(workdir, batchconfig.cluster, "CentOS8"), runcmd)
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
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default="", help="POWHEG input")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=0, help="Number of events (default: 0:=Default number of events in powheg.input)")
    parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=-1, help="Number of slots")
    parser.add_argument("-m", "--minslot", metavar="MINSLOT", type=int, default=0, help="Min. slot ID")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="all", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-g", "--grids", metavar="GRIDS", type=str, default="NONE", help="Old grids (default: NONE")
    parser.add_argument("--process", metavar="PROCESS", type=str, default="dijet", help="Process (default: dijet)")
    parser.add_argument("--scalereweight", action="store_true", help="Run scale reweight")
    parser.add_argument("--minpdf", metavar="MINPDF", type=int, default=-1, help="PDF reweight min. PDF")
    parser.add_argument("--maxpdf", metavar="MAXPDF", type=int, default=-1, help="PDF reweight max. PDF")
    parser.add_argument("--minweightid", metavar="MINWEIGHTID", type=int, default=0, help="PDF reweight min weight ID")
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

    scalereweight = args.scalereweight
    pdfreweight = args.minpdf > -1 and args.maxpdf > -1
    if not scalereweight and not pdfreweight:
        if not len(args.input):
            logging.info("powheg.input must be provided in non-reweight mode")

    simconfig = SimConfig()
    simconfig.workdir = args.workdir
    simconfig.gridrepository = args.grids
    simconfig.nevents = args.events
    simconfig.powheginput = args.input
    simconfig.process = args.process
    simconfig.powhegversion = args.version
    if args.scalereweight:
        simconfig.set_scalereweight(True)
    if args.minpdf > -1 and args.maxpdf > -1:
        simconfig.minpdf = args.minpdf
        simconfig.maxpdf = args.maxpdf
        simconfig.minID = args.minweightid

    njobs = args.njobs
    minslot = args.minslot
    if simconfig.is_scalereweight() or simconfig.is_pdfreweight():
        if njobs == -1:
            # auto-determine number of slots
            indexmin, indexmax = find_index_of_input_file_range(os.path.join(args.workdir, f"POWHEG_{simconfig.powhegversion}"))
            logging.debug(f"Min. index: {indexmin}, max index: {indexmax}")
            if indexmin == -1 or indexmax == -1:
                logging.error("Didn't find slot dirs with pwgevents.lhe in %s", args.workdir)
                sys.exit(1)
            minslot = indexmin
            njobs = indexmax - indexmin + 1
    else:
        if njobs == -1:
            logging.error("Number of jobs must be provided")
            sys.exit(1)

    simconfig.minslot = minslot

    batchconfig = SlurmConfig()
    batchconfig.cluster = cluster
    batchconfig.partition = partition
    batchconfig.njobs = njobs
    batchconfig.memory = args.mem
    batchconfig.hours = args.hours

    if not simconfig.is_scalereweight() and not simconfig.is_pdfreweight():
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
	
