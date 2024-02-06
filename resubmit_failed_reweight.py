#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.checkjob import submit_checks, submit_check_slot
from helpers.cluster import get_cluster, get_default_partition
from submit_powheg import submit_job
from helpers.slurm import SlurmConfig, submit
from helpers.simconfig import SimConfig

class SlotIndexException(Exception):

    def __init__(self, slotname: str):
        self.__slotname = slotname

    def __str__(self) -> str:
        return f"Cannot determine slot index from {self.__slotname}"

    def get_slotname(self) -> str:
        return self.__slotname

class Corruptedfile(object):

    def __init__(self, fname: str, missingweights: list):
        self.__fname = fname
        self.__missingweights = missingweights

    def set_filename(self, fname: str):
        self.__fname = fname

    def set_missingweights(self, missingweights: list):
        self.__missingweights = missingweights

    def add_missing_weight(self, weighID: str):
        self.__missingweights.append(weighID)

    def get_missing_weights_scale(self):
        result = []
        for weightID in self.__missingweights:
            if weightID == "main":
                continue
            if not weightID.isdigit():
                continue
            indexweight = int(weightID)
            if indexweight > 0 and indexweight <= 7:
                result.append(indexweight)
        return result

    def get_missing_weights_pdf(self):
        result = []
        for weightID in self.__missingweights:
            if weightID == "main":
                continue
            if not weightID.isdigit():
                continue
            indexweight = int(weightID)
            if indexweight >= 8:
                result.append(indexweight)
        return result

    def get_slotID(self) -> int:
        slotdir = os.path.dirname(self.__fname)
        slotID = os.path.basename(slotdir)
        if slotID.isdigit():
            logging.debug("Found slot: %s", slotID)
            return int(slotID)
        raise SlotIndexException(slotID)

class CheckResults(object):

    def __init__(self):
        self.__expectweights = []
        self.__corrupted = []

    def add_expectweight(self, weightID: str):
        self.__expectweights.append(weightID)

    def set_expectweights(self, weightIDs: list):
        self.__expectweights = weightIDs

    def add_corruptedfile(self, filename: str, missingweights: list):
        self.__corrupted.append(Corruptedfile(filename, missingweights))

    def get_corruptedfiles(self) -> list:
        return self.__corrupted


def clean_slortdir(slotdir: str):
    # remove existing reweight file and semaphore
    logging.debug("Cleaning %s" %slotdir)
    rwgtfile = os.path.join(slotdir, "pwgevents-rwgt.lhe")
    if os.path.exists(rwgtfile):
        os.remove(rwgtfile)
    semaphore = os.path.join(slotdir, "pwgsemaphore.txt")
    if os.path.exists(semaphore):
        os.remove(semaphore)

def get_failed_slots(checkfile: str) -> CheckResults:
    result = CheckResults()
    markerstart = "pwgevents.lhe files with missing weights:"
    markerend = "----------------------------------------"
    with open(checkfile, "r") as checkreader:
        startfailed = False
        for line in checkreader:
            line = line.replace("\n", "")
            line = line.replace("[INFO]: ", "")
            if "Found weight IDs:" in line:
                weightidstring = line.replace("Found weight IDs:","").lstrip().rstrip()
                weights = weightidstring.split(",")
                for weight in weights:
                    result.add_expectweight(weight.lstrip().rstrip())
                continue
            if startfailed:
                if markerend in line:
                    startfailed = False
                    break
                else:
                    separator = line.find(" ")
                    fname = line[:separator]
                    missing = line[separator+1:]
                    missingweightstring = missing[missing.find(":")+1:missing.rfind(")")]
                    missingweights = []
                    for weightID in missingweightstring.split(","):
                        missingweights.append(weightID.lstrip().rstrip())
                    result.add_corruptedfile(fname, missingweights)
            else:
                if markerstart in line:
                    startfailed = True
        checkreader.close()
    return result


def next_iteration_resubmit(repo: str, cluster: str, workdir: str, partition: str, version: str, process: str, mem: int, hours: int, scalereweight: bool, minID: int, minpdf: int, dependency: int = None) -> int:
    executable = os.path.join(repo, "resubmit_failed_reweight.py")
    resubmit_cmd = f"{executable} {workdir} -p {partition} -v {version} --process {process} --mem {mem} --hours {hours}"
    if scalereweight:
        resubmit_cmd += " --scalereweight"
    else:
        resubmit_cmd += f" --minID {minID} --minpdf {minpdf}"
    resubmit_wrapper = os.path.join(workdir, "stage", "resubmit_wrapper.sh")
    if os.path.exists(resubmit_wrapper):
        os.remove(resubmit_wrapper)
    with open(resubmit_wrapper, "w") as wrapperwriter:
        wrapperwriter.write("#! /bin/bash\n")
        wrapperwriter.write(f"export PYTHONPATH=$PYTHONPATH:{repo}\n")
        wrapperwriter.write("echo Submitting next iteration\n")
        wrapperwriter.write(f"{resubmit_cmd}\n")
        wrapperwriter.close()
    os.chmod(resubmit_wrapper, 0o755)
    jobname = "resubmit_iteration"
    logfile = os.path.join(workdir, "logs", "resubmit_reweight.log")
    dependencies = []
    if dependency is not None:
        dependencies = [dependency]
    return submit(resubmit_wrapper, cluster, jobname, logfile, partition, timelimit="00:10:00", dependency = dependencies)


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
                pwhgjob = submit_job(simconf, batchconfig, True)
                checkjob = submit_check_slot(cluster, repo, workdir, slotID, partition, pwhgjob)
                jobids_check.append(checkjob)
        except SlotIndexException as e:
            logging.error(e)   
    if len(jobids_check):
        jobids_check = submit_checks(cluster, repo, workdir, partition, jobids_check, False, True)
        logging.info("Submitting final check job under job ID %d", jobids_check)
        jobid_resubmit = next_iteration_resubmit(repo, cluster, workdir, partition, args.version, args.process, args.mem, args.hours, args.scalereweight, args.minID, args.minpdf, jobids_check)