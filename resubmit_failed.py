#! /usr/bin/env python3

import argparse
import logging
import os
import shutil
import sys

from submit_powheg import submit_job
from helpers.checkjob import submit_checks, submit_check_slot
from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging
from helpers.slurm import SlurmConfig
from helpers.simconfig import SimConfig

def clean_slotdir(slotdir: str):
    if os.path.exists(slotdir):
        shutil.rmtree(slotdir)

def parse_powheg_config(workdir: str, slot: int) ->SimConfig:
    logfile = os.path.join(workdir, "logs", f"joboutput{slot}.log")
    if not os.path.exists(logfile):
        logging.error("Logfile for slot %d does not exist, cannot create POWHEG config")
        return None
    config = SimConfig()
    config.workdir = os.path.dirname(workdir)
    config.minslot = slot
    with open(logfile, "r") as logreader:
        for line in logreader:
            line = line.replace("\n", "")
            if "Request POWHEG version:" in line:
                line = line.replace("Request POWHEG version:", "")
                config.powhegversion = line.lstrip().rstrip()
                continue
            if line.find("Running:") == 0:
                line = line.replace("Running: ", "")
                tokens = line.split(" ")
                indextoken = 2
                while indextoken < len(tokens):
                    if indextoken == 2:
                        config.powheginput = tokens[indextoken]
                    elif tokens[indextoken] == "-g":
                        config.gridrepository = tokens[indextoken+1]
                    elif tokens[indextoken] == "-e":
                        config.nevents = int(tokens[indextoken+1])
                    elif tokens[indextoken] == "-t":
                        config.process = tokens[indextoken+1]

                    if tokens[indextoken].startswith("-"):
                        indextoken += 2
                    else:
                        indextoken += 1
    return config

def submit_slot(workdir: str, slot: int, simparams: SimConfig, slurparams: SlurmConfig):
    logging.info("Resubmitting slot: %d", slot)
    clean_slotdir(os.path.join(workdir, "%04d" %slot))
    return submit_job(simparams, slurparams, True)

def get_failed_slots(checkfile: str) -> list:
    failedslots = []
    markerstart = "Incomplete pwgevents.lhe files:"
    markerend = "----------------------------------------"
    with open(checkfile, "r") as checkreader:
        startfailed = False
        for line in checkreader:
            line = line.replace("\n", "")
            line = line.replace("[INFO]: ", "")
            if startfailed:
                if markerend in line:
                    startfailed = False
                    break
                else:
                    slotdir = os.path.dirname(line)
                    slotID = os.path.basename(slotdir)
                    if slotID.isdigit():
                        logging.info("Found slot: %s", slotID)
                        failedslots.append(int(slotID))
            else:
                if markerstart in line:
                    startfailed = True
        checkreader.close()
    return sorted(failedslots)

if __name__ == "__main__":
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    parser = argparse.ArgumentParser("resubmit_failed.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("--debug", action="store_true", help="debug mode")
    parser.add_argument("--test", action="store_true", help="test mode")

    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default="default", help="POWHEG input")
    parser.add_argument("-g", "--grids", metavar="GRIDS", type=str, default="default", help="Old grids (default: NONE")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="default", help="POWEHG version")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=0, help="Number of events (default: 0:=Default number of events in powheg.input)")
    parser.add_argument("--process", metavar="PROCESS", type=str, default="default", help="Process (default: dijet)")
    args = parser.parse_args()
    setup_logging(args.debug)

    cluster = get_cluster()
    if cluster == None:
        logging.error("Failed to detect computing cluster")
        sys.exit(1)
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    workdir = os.path.abspath(args.workdir)
    checkfile = os.path.join(workdir, "checksummary_pwgevents.log")
    if not os.path.exists(checkfile):
        logging.error("Working directory %s does not provide a checksummary_pwgevents.log")
        sys.exit(1)

    slots = get_failed_slots(checkfile)
    if not len(slots):
        logging.error("No failed slot found in %s, no slots to be resubmitted", checkfile)
        sys.exit(1)

    batchconfig = SlurmConfig()
    batchconfig.cluster = cluster
    batchconfig.partition = partition
    batchconfig.njobs = 1 # submission per slot
    batchconfig.memory = args.mem
    batchconfig.hours = args.hours

    jobids_check = []
    for slot in slots:
        simconfig = parse_powheg_config(workdir, slot)
        if not simconfig:
            logging.error("Failed to parse simulation params for slot: %d", slot)
            continue
        if args.events != 0:
            simconfig.nevents = args.events
        if args.process != "default":
            simconfig.process = args.process
        if args.grids != "default":
            simconfig.gridrepository = args.grids
        if args.input != "default":
            simconfig.powheginput = args.input
        if args.version != "default":
            simconfig.powhegversion = args.version
        simconfig.print()
        if not args.test:
            pwhgjob = submit_slot(workdir, slot, simconfig, batchconfig)
            checkjob = submit_check_slot(cluster, repo, workdir, slot, partition, pwhgjob)
            jobids_check.append(checkjob)
        else:
            # test mode: try only parsing the simulation configuration
            simconfig = parse_powheg_config(workdir, slot)
    if len(jobids_check):
        submit_checks(cluster, repo, workdir, partition, jobids_check, False, True)
