#! /usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
import time

from helpers.pwgeventsparser import pwgeventsparser
from helpers.pythiaparams import PythiaParams
from helpers.setup_logging import setup_logging
from helpers.timehelpers import log_elapsed_time

class PythiaRunner(object):

    def __init__(self):
        self.__workdir = ""
        self.__powhegevents = ""
        self.__macro = ""
        self.__params = PythiaParams()

    def set_workdir(self, workdir: str):
        self.__workdir = workdir

    def set_eventfile(self, eventfile: str):
        self.__powhegevents = eventfile

    def set_macro(self, macro: str):
        self.__macro = macro

    def get_pythia_parameter(self) -> PythiaParams():
        return self.__params

    def set_pythia_parameter(self, params: PythiaParams):
        self.__params = params
        
    def initialise(self) -> bool:
        if not os.path.exists(self.__macro):
            logging.error("Analysis macro does not exist")
            return False
        if not os.path.exists(self.__powhegevents):
            logging.error("POWHEG events do not exist")
            return False
        if not self.__is_powheg_events_OK(self.__powhegevents):
            logging.error("POWHEG events not consistent")
            return False
        if not os.path.exists(self.__workdir):
            os.makedirs(self.__workdir, 0o755)
        return True

    def run(self):
        os.chdir(self.__workdir)
        cmd = f"root -l -b -q \'{self.__macro}(\"{self.__powhegevents}\")\'"
        self.__prepare_environment()
        logfile = os.path.join(self.__workdir, "pythia.log")
        with open(logfile, "w") as logwriter:
            subprocess.call(cmd, shell=True, stdout=logwriter, stderr=subprocess.STDOUT)
            logwriter.close()
        
    def __prepare_environment(self):
        self.__params.export_environment()

    def __is_powheg_events_OK(self, powheginput: str) -> bool:
        parser = pwgeventsparser(powheginput)
        parser.parse()
        events = parser.get_eventinfos()
        if not events.get_nevents():
            logging.error("POWHEG event file %s does not contain any event", powheginput)
            return False
        if not events.has_closingmarker():
            logging.warning("POWHEG event file %s incomplete, still try to process", powheginput)
        return True

def decodeChunkID(eventfile: str) -> str:
    chunkdir = os.path.basename(os.path.dirname(os.path.abspath(eventfile)))
    if chunkdir.isdigit():
        return chunkdir
    return ""

def runForEventFile(workdir: str, eventfile: str, macro: str, params: PythiaParams):
    logging.info("Processing POWHEG file: %s", eventfile)
    currentworkdir = workdir
    chunkdir = decodeChunkID(eventfile)
    if len(chunkdir):
        logging.info("Decoded chunk ID: %s", chunkdir)
        currentworkdir = os.path.join(workdir, chunkdir) 
    else:
        logging.info("No chunk ID dedcoded")
    processor = PythiaRunner()
    processor.set_eventfile(eventfile)
    processor.set_macro(macro)
    processor.set_pythia_parameter(params)
    processor.set_workdir(currentworkdir)
    if processor.initialise():
        starttime = time.time()
        processor.run()
        endtime = time.time()
        log_elapsed_time("PYTHIA processing", starttime, endtime)
    else:
        logging.error("Failed initializing PYTHIA task executor, cannot run")

def run_filelist(workdir: str, filelist: str, macro: str, params: PythiaParams):
    with open(filelist, "r") as listreader:
        for currentfile in listreader:
            currentfile = currentfile.rstrip("\n")
            if currentfile.endswith(".lhe"):
                runForEventFile(workdir, currentfile, macro, params)
        listreader.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("pythia_runner.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="WORKING directory")
    parser.add_argument("eventfile", metavar="EVENTFILE", type=str, help="pwgevents.lhe file to be analysed")
    parser.add_argument("macro", metavar="MACRO", type=str, help="ROOT macro for PYTHIA event generation and analysis")
    parser.add_argument("-c", "--config", metavar="CONFIG", type=str, default="", help="PYTHIA settings")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    starttime = time.time()

    params = PythiaParams()
    params.deserialize(args.config)
    params.log()

    eventfile = args.eventfile
    if eventfile == "slotfilelist":
        slot = os.getenv("SLOT")
        if slot:
            filelistname = os.path.join(args.workdir, "filelists", f"pwhgin{slot}.txt")
            if os.path.exists(filelistname):
                run_filelist(args.workdir, filelistname, args.macro, params)
            else:
                logging.error("Expected filelist for slot %d (%s) does not exist", slot, filelistname)
        else:
            logging.error("Slot-based filelist requested, but slot ID not defined")
            sys.exit(1)
    if ".txt" in eventfile:
        # Handle filelist case
        run_filelist(args.workdir, eventfile, args.macro, params)
    else:
        # Single pwgevents.lhe file
        runForEventFile(args.workdir, eventfile, args.macro, params)

    endtime = time.time()
    log_elapsed_time("Job", starttime, endtime)
    