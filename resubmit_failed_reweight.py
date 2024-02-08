#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.checkjob import submit_checks, submit_check_slot
from helpers.cluster import get_cluster, get_default_partition
from helpers.pwgsubmithandler import submit_simulation, UninitException
from helpers.resubmithandler import get_failed_slots, next_iteration_resubmit, SlotIndexException
from helpers.simconfig import SimConfig
from helpers.slurm import SlurmConfig

def clean_slortdir(slotdir: str):
    # remove existing reweight file and semaphore
    logging.debug("Cleaning %s" %slotdir)
    rwgtfile = os.path.join(slotdir, "pwgevents-rwgt.lhe")
    if os.path.exists(rwgtfile):
        os.remove(rwgtfile)
    semaphore = os.path.join(slotdir, "pwgsemaphore.txt")
    if os.path.exists(semaphore):
        os.remove(semaphore)

if __name__ == "__main__":
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    parser = argparse.ArgumentParser("resubmit_failed_reweight.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="FromALICE", help="POWHEG version")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=24, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-t", "--test", action="store_true", help="Test mode")
    parser.add_argument("--process", metavar="PROCESS", type=str, default="dijet", help="POWHEG process")
    parser.add_argument("--scalereweight", action="store_true", help="Scale reweight")
    parser.add_argument("--minID", metavar="MINID", type=int, default=-1, help="Min. weight ID PDF reweighting")
    parser.add_argument("--minpdf", metavar="MINPDF", type=int, default=-1, help="Min. pdf PDF reweight")
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
    failedfiles = get_failed_slots(checkfile).get_corruptedfiles()
    
    batchconfig = SlurmConfig()
    batchconfig.cluster = cluster
    batchconfig.partition = partition
    batchconfig.njobs = 1 # submission per slot
    batchconfig.memory = args.mem
    batchconfig.hours = args.hours

    simconf = SimConfig()
    simconf.powhegversion = args.version
    simconf.powheginput = None
    simconf.process = args.process
    simconf.workdir = os.path.dirname(workdir)

    jobids_check = []
    for failed in failedfiles:
        try:
            slotID = failed.get_slotID()
            logging.info("Found slot: %s", slotID)
            simconf.minslot = failed.get_slotID()
            if args.scalereweight:
                if len(failed.get_missing_weights_scale()):
                    simconf.set_scalereweight(True)
            else:
                foundpdfweights = sorted(failed.get_missing_weights_pdf())
                weightstring = ""
                for weight in foundpdfweights:
                    if len(weightstring):
                        weightstring += ", "
                    weightstring += f"{weight}"
                logging.debug("Found PDF weights: %s", weightstring)
                minpdf = args.minpdf + (foundpdfweights[0] - args.minID)
                maxpdf = minpdf + (foundpdfweights[len(foundpdfweights)-1] - foundpdfweights[0])
                simconf.minID = foundpdfweights[0]
                simconf.minpdf = minpdf
                simconf.maxpdf = maxpdf
                logging.info("Found missing: min: %d / max: %d PDF, min. ID: %d", minpdf, maxpdf, simconf.minID)
            logging.info("Submitting slot: %d", simconf.minslot)
            if not args.test:
                clean_slortdir(os.path.join(workdir, "%04d" %slotID))
                pwhgjob = submit_simulation(repo, simconf, batchconfig, True)
                checkjob = submit_check_slot(cluster, repo, workdir, slotID, partition, pwhgjob)
                jobids_check.append(checkjob)
        except SlotIndexException as e:
            logging.error(e)   
        except UninitException as e:
            logging.error(e)
    if len(jobids_check):
        jobids_check_final = submit_checks(cluster, repo, workdir, partition, jobids_check, False, True)
        logging.info("Submitting final check job under job ID %d", jobids_check_final["final"][0])
        jobid_resubmit = next_iteration_resubmit(repo, cluster, workdir, partition, args.version, args.process, args.mem, args.hours, args.scalereweight, args.minID, args.minpdf, jobids_check_final["final"][0])