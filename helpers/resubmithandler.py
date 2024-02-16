#! /usr/bin/env python3

import logging
import os

from helpers.slurm import submit

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

def get_incomplete_slots(checkfile: str) -> list:
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