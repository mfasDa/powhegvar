#! /usr/bin/env python3

import argparse
import logging
import os
import random
import shutil
import subprocess
import sys
import time

from helpers.setup_logging import setup_logging
from helpers.reweighting import create_config_pdfreweight, create_config_scalereweight
from helpers.events import create_config_nevens

class POWHEG_runner:

    def __init__(self, workdir: str, pwginput):
        self.__workdir = workdir
        self.__pwginput = pwginput
        self.__reweightscale = False
        self.__reweightpdf = False
        self.__gridrepository = ""
        self.__minpdf = -1
        self.__maxpdf = -1
        self.__minid = -1
        self.__events = -1
        self.__workdirInitialized = False
        self.__powhegtype = ""

    def set_workdir(self, workdir: str):
        self.__workdir = workdir
        
    def set_pwginput(self, pwginput: str):
        self.__pwginput = pwginput
    
    def set_events(self, events: int):
        self.__events = events

    def set_scalereweight(self, minID: int):
        self.__reweightscale = True
        self.__minid = minID

    def set_pdfreweight(self, minpdf:int, maxpdf:int, minID: int):
        self.__reweightpdf = True
        self.__minpdf = minpdf
        self.__maxpdf = maxpdf
        self.__minid = minID

    def set_gridrepository(self, gridrepository: str):
        self.__gridrepository = gridrepository

    def set_powhegtype(self, pwhgtype):
        if not self.__is_valid_pwhgtype(pwhgtype):
            logging.error("Selected POWHEG type %s invalid", pwhgtype)
        else:
            self.__powhegtype = pwhgtype

    def get_workdir(self) -> str:
        return self.__workdir

    def get_pwginput(self) -> str:
        return self.__pwginput

    def get_gridrepository(self) -> str:
        return self.__gridrepository

    def get_powhegtype(self) -> bool:
        return self.__powhegtype

    def get_events(self) -> int:
        return self.__events

    def is_scalereweight(self) -> bool:
        return self.__reweightscale 

    def is_pdfreweight(self) -> bool:
        return self.__reweightpdf

    def is_reweight(self) -> bool:
        return self.is_scalereweight() or self.is_pdfreweight()

    def get_minID(self) -> int:
        return self.__minid

    def get_minpdf(self) -> int:
        return self.__minpdf

    def get_maxpdf(self) -> int:
        return self.__maxpdf

    def is_useexistinggrids(self) -> bool:
        return len(self.__gridrepository) > 0

    def is_powhegtype_set(self) -> bool:
        return len(self.__powhegtype) > 0

    pwginput = property(fget=get_pwginput, fset=set_pwginput)
    workdir = property(fget=get_workdir, fset=set_workdir)
    gridrepository = property(fget=get_gridrepository, fset=set_gridrepository)
    events = property(fget=get_events, fset=set_events)

    def init(self) -> bool:
        self.__prepare_workdir()
        return self.__workdirInitialized

    def run(self) -> bool:
        if not self.is_powhegtype_set():
            logging.error("No valid POWHEG type defined, cannot run ...")
            return False
        if not self.__workdirInitialized:
            logging.error("Working directory not properly initialized, cannot run")
        logging.info("Workdir %s properly initialized, ready for running POWHEG job ...", self.__workdir)
        if not self.is_reweight():
            if self.__workdir_has_pwgevents():
                logging.error("pwgevents.lhe already found in working directory %s for non-reweight jon - cannot run ...")
                return False
            logging.info("Running standard powheg job")
            self.__run_powhegjob("pwhg.log")
        else:
            if self.is_scalereweight():
                self.__run_scalereweight()
            elif self.__run_pdfreweight():
                self.__run_pdfreweight()
        return True

    def __run_scalereweight(self):
        os.chdir(self.__workdir)
        currentid = self.__minid
        variations = [0.5, 1., 2.]
        for indexMuR in range(0, 3):
            variationMuR = variations[indexMuR]
            for indexMuF in range(0, 3):
                variationMuF = variations[indexMuF]
                self.__list_workdir()
                if self.__workdir_has_reweightevents():
                    logging.error("pwgevents-reweight.lhe found in workdir %s in weighting mode, cannot run ...")
                    return
                if indexMuR == 1 and indexMuF == 1:
                    logging.info("Skipping default variation muf = mur = 1")
                    continue
                logging.info("Running variation mur = %f, muf = %f", variationMuR, variationMuF)
                create_config_scalereweight(self.__pwginput, os.path.join(self.__workdir, "powheg.input"), variationMuF, variationMuR, currentid)
                vartag = "mur%d_muf%d" %(int(variationMuR*10.), int(variationMuF*10.))
                self.__run_powhegjob(f"pwhg_{vartag}.log")
                if self.__workdir_has_reweightevents():
                    self.__stage_reweight()
                if self.__workdir_has_powheginput():
                    self.__stage_powheginput(vartag)
                currentid += 1

    def __run_pdfreweight(self):
        os.chdir(self.__workdir)
        currentid = self.__minid
        currentpdf = self.__minpdf
        while currentpdf <= self.__maxpdf:
            self.__list_workdir()
            if self.__workdir_has_reweightevents():
                logging.error("pwgevents-reweight.lhe found in workdir %s in weighting mode, cannot run ...", self.__workdir)
                return
            logging.info("Running pdf variation %d with weight ID %d", currentpdf, currentid)
            create_config_pdfreweight(self.__pwginput, os.path.join(self.__workdir, "powheg.input"), currentpdf, currentid)
            self.__run_powhegjob(f"pwgh_PDF{currentpdf}.log")
            if self.__workdir_has_reweightevents():
                self.__stage_reweight()
            if self.__workdir_has_powheginput():
                self.__stage_powheginput(f"PDF{currentpdf}")
            currentpdf += 1
            currentid += 1

    def __run_powhegjob(self, logfile):
        os.chdir(self.__workdir)
        self.__list_workdir()
        self.__set_seed()
        command = f"pwhg_main_{self.__powhegtype} &> {logfile}"
        logging.debug("Running: %s", command)
        subprocess.call(command, shell=True)

    def __list_workdir(self):
        content = os.listdir(os.getcwd())
        first = True
        contentstring = ""
        for entry in content:
            if not first:
                contentstring += ","
            else:
                first = False
            contentstring += f" {entry}"
        logging.info("Content of workdir: %s", contentstring)

    def __is_valid_pwhgtype(self, pwhgtype):
        types = ["dijet", "directphoton", "hvq", "W", "Z"]
        if pwhgtype in types:
            return True
        return False

    def __get_gridfiles(self):
        return ["pwggrid.dat", "pwgubound.dat", "pwgxgrid.dat"]

    def __find_gridfiles_parallelstage(self):
        filter = lambda x: x.startswith("pwggrid-") or x.startswith("pwgubound-") or x.startswith("pwggridinfo-btl-xg")
        return [x for x in os.listdir(self.__gridrepository) if filter(x)]

    def __check_gridfile_parallel(self):
        if not os.path.exists(self.__gridrepository):
            return False
        files_repository = self.__find_gridfiles_parallelstage()
        logging.info("found %d gridfiles parallel stage", len(files_repository))
        grids = [x for x in files_repository if x.startswith("pwggrid-")]
        ubounds = [x for x in files_repository if x.startswith("pwgubound-")]
        gridinfos = [x for x in files_repository if x.startswith("pwggridinfo-btl-xg")]
        if len(grids) > 0 and len(ubounds) > 0 and len(gridinfos) > 0:
            if len(grids) == len(ubounds):
                if len(gridinfos) % len(grids) == 0:
                    logging.info("Found PWG grids from parallel stage: %d grid, %d ubounds and %d gridinfos", len(grids), len(ubounds), len(gridinfos))
                    return True
                else:
                    logging.error("Number of gridinfos not multiple of number of grids (%d gridinfos, %d grids)", len(gridinfos), len(grids))
                    return False
            else:
                logging.error("Inconsistent grid files from parallel stage: %d grids, %d ubounds, %d gridinfos", len(grids), len(ubounds), len(gridinfos))
                return False
        else:
            logging.debug("Either one or several grid files missing")
            return False

    def __check_gridfiles(self) -> bool:
        if not os.path.exists(self.__gridrepository):
            return False
        gridfiles = self.__get_gridfiles()
        file_in_gridrepo = os.listdir(self.__gridrepository)
        files_missing = []
        for fl in gridfiles:
            if not fl in file_in_gridrepo:
                files_missing.append(fl)
        if len(files_missing):
            logging.error("The following grid files have been missing: ")
            logging.error("=======================================================")
            for fl in files_missing:
                logging.error(fl)
            return False
        return True

    def __fetch_oldgrids(self, parallel_mode: bool):
        if not os.path.exists(self.__gridrepository):
            logging.error("Repository with grids not existing")
            return
        gridfiles = []
        if parallel_mode:
            files_repository = self.__find_gridfiles_parallelstage()
            grids = [x for x in files_repository if x.startswith("pwggrid-")]
            ubounds = [x for x in files_repository if x.startswith("pwgubound-")]
            gridinfos = [x for x in files_repository if x.startswith("pwggridinfo-btl-xg")]
            # select all grids and ubounds
            for fl in grids:
                gridfiles.append(fl)
            for fl in ubounds:
                gridfiles.append(fl)
            # select files from the largest xgrid iteration
            lastiteration = -1
            for info in gridinfos:
                xgiter = info.split("-")[2]
                xgiterval = int(xgiter.replace("xg",""))
                if xgiterval > lastiteration:
                    lastiteration = xgiterval
            logging.info("Last xgrid iteration: %d", lastiteration)
            for fl in [x for x in gridinfos if f"xg{lastiteration}" in x]:
                gridfiles.append(fl)
        else:
            gridfiles = self.__get_gridfiles()
        for fl in gridfiles:
            self.__copy_to_workdir(os.path.join(self.__gridrepository, fl), fl)

    def __check_settings(self):
        if self.is_reweight() and self.is_useexistinggrids():
            logging.error("Cannot run with old grids in reweight mode")
            return False
        return True

    def __check_pwginput(self):
        return os.path.exists(self.__pwginput)

    def __workdir_has_file(self, filename: str):
        return os.path.exists(os.path.join(self.__workdir, filename))

    def __workdir_has_pwgevents(self):
        return self.__workdir_has_file("pwgevents.lhe")

    def __workdir_has_reweightevents(self):
        return self.__workdir_has_file("pwgevents-rwgt.lhe")

    def __workdir_has_powheginput(self):
        return self.__workdir_has_file("powheg.input")

    def __workdir_filerename(self, oldfile: str, newfile:str):
        os.rename(os.path.join(self.__workdir, oldfile), os.path.join(self.__workdir, newfile))

    def __stage_reweight(self):
        self.__workdir_filerename("pwgevents-rwgt.lhe", "pwgevents.lhe")

    def __stage_powheginput(self, variation: str):
        self.__workdir_filerename("powheg.input", f"powheg_{variation}.input")

    def __copy_to_workdir(self, inputfile: str, file_in_workdir: str):
        shutil.copyfile(inputfile, os.path.join(self.__workdir, file_in_workdir))

    def __set_seed(self):
        randomseed = random.randint(0, 32767)
        logging.info("Using random seed: %d", randomseed)
        with open(os.path.join(self.__workdir, "powheg.input"), "a") as configwriter:
            configwriter.write("iseed %d\n" %randomseed)
            configwriter.close()

    def __prepare_workdir(self):
        if not self.__check_settings():
            logging.error("Cannot initialize workdir due to invalid configuration")
            return
        if not self.__check_pwginput():
            logging.error("Powheg input not existing, cannot run ...")
            return
        if not os.path.exists(self.__workdir):
            if self.is_reweight():
                logging.error("running in reweight mode, but workdir not existing, cannot run ...")
                return
            else:
                logging.info("Creating new working directory %s", self.__workdir)
                os.mkdir(self.__workdir, 0o755)
        if self.is_reweight():
            if not self.__workdir_has_pwgevents():
                logging.error("Require existing pwgevents.lhe in workdir for reweight mode")
                return
            if self.__workdir_has_reweightevents():
                logging.error("Found unexpected file pwgevents-rwgt.lhe for reweighting mode, processing might crash, cannot run ...")
                return
            self.__stage_powheginput("base")
        else:
            if len(os.listdir(self.__workdir)):
                logging.error("Found non-empty working directory in non-reweight mode, cannot run ...")
                return
            if self.__events > 0:
                # Need to create a new configuration setting the number of events 
                create_config_nevens(self.__pwginput, os.path.join(self.__workdir, "powheg.input"), self.__events)
            else:
                # Use existing configuration with the default number of events
                self.__copy_to_workdir(self.__pwginput, "powheg.input")
        if self.is_useexistinggrids():
            parallelmode = False
            if not self.__check_gridfile_parallel():
                if not self.__check_gridfiles():
                    logging.error("Request running with existing grids, but not all expected files found, cannot run ...")
                    return
            else:
                parallelmode = True
            logging.info("Found grid files in %s (%s mode)", self.__gridrepository, "parallel" if parallelmode else "sequential") 
            self.__fetch_oldgrids(parallelmode)
        self.__workdirInitialized = True
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser("powheg_runner.py", description="Frontent for POWHEG calculations")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Processing directory")
    parser.add_argument("input", metavar="POWHEGINPUT", type=str, help="Full path of powheg input file")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=0, help="Number of events")
    parser.add_argument("-t", "--type", metavar="POWHEGTYPE", type=str, default="dijet", help="POWHEG type, can be dijet, directphoton, hvq, W or Z (default: dijet)")
    parser.add_argument("-g", "--gridfiledir", metavar="GRIDFILEDIR", type=str, default="", help="Location of gridfile (in case of running with existing grids)")
    parser.add_argument("--minpdf", metavar="MINPDF", type=int, default=-1, help="Min. pdf (in case of PDF reweighting mode)")
    parser.add_argument("--maxpdf", metavar="MAXPDF", type=int, default=-1, help="Max. pdf (in case of PDF reweighting mode)")
    parser.add_argument("--minid", metavar="MINID", type=int, default=-1, help="Min. weight ID (in case of scale or PDF reweighting)")
    parser.add_argument("--slot", metavar="SLOT", type=int, default=-1, help="Slot (in case of multi-processing)")
    parser.add_argument("-s", "--scalereweight", action="store_true", help="Run scale reweighting mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    scalereweight = args.scalereweight
    pdfreweight = args.minpdf > -1 and args.maxpdf > -1
    if scalereweight and pdfreweight:
        logging.error("Cannot run scale and pdf reweighting in the same job ...")
        sys.exit(1)
    if scalereweight or pdfreweight:
        if not args.minid > -1:
            logging.error("A valid minid must be specified in reweighting mode")
            sys.exit(2)

    workdir = os.path.abspath(args.workdir)
    workdirmessage = f"Using working directory: {workdir}"
    slot = args.slot
    if slot > -1:
        workdir = os.path.join(workdir, "%04d" %slot)
        workdirmessage = f"Using working directory: {workdir} (slot {slot})"
    logging.info(workdirmessage)

    processor = POWHEG_runner(workdir, os.path.abspath(args.input))
    processor.set_powhegtype(args.type)
    if scalereweight:
        processor.set_scalereweight(args.minid)
    if pdfreweight:
        processor.set_pdfreweight(args.minpdf, args.maxpdf, args.minid)
    if len(args.gridfiledir):
        processor.set_gridrepository(os.path.abspath(args.gridfiledir))
    if args.events > 0:
        processor.set_events(args.events)
    if not processor.init():
        logging.error("Error during initialization of the POWHEG processor, cannot run the simulation ...")
        sys.exit(3)
    else:
        starttime = time.time()
        logging.info("POWHEG processor initialized, running the simulation")
        if processor.run():
            endtime = time.time()
            elapsed_seconds = endtime - starttime
            hours = elapsed_seconds / 3600
            minutes = (elapsed_seconds / 60) % 60
            seconds = elapsed_seconds % 60
            logging.info("POWHEG processing finished, took %d:%d:%d (%d seconds total)", hours, minutes, seconds, elapsed_seconds)
        else:
            logging.info("Error in POWHEG processing")
            sys.exit(4)