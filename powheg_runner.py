#! /usr/bin/env python3

import argparse
import logging
import os
import random
import shutil
import subprocess
import sys
import time

from helpers.events import create_config_nevens
from helpers.gridarchive import gridarchive, init_archive
from helpers.powheg import is_valid_process
from helpers.pwgeventsparser import pwgeventsparser, pwgevents_info
from helpers.pwsemaphore import pwsemaphore, has_semaphore
from helpers.setup_logging import setup_logging
from helpers.reweighting import create_config_pdfreweight, create_config_scalereweight, build_weightID_scalereweight, build_weightID_pdfreweight 

class POWHEG_runner:

    def __init__(self, workdir: str, pwginput):
        self.__workdir = workdir
        self.__pwginput = pwginput
        self.__reweightscale = False
        self.__reweightpdf = False
        self.__gridrepository = ""
        self.__gridarchive: gridarchive = None
        self.__minpdf = -1
        self.__maxpdf = -1
        self.__minid = -1
        self.__events = -1
        self.__workdirInitialized = False
        self.__powhegtype = ""
        self.__foundweights = []
        self.__slot = 0
        self.__stage = 0
        self.__xgriditer = 0

    def set_workdir(self, workdir: str):
        self.__workdir = workdir
        
    def set_pwginput(self, pwginput: str):
        self.__pwginput = pwginput
    
    def set_events(self, events: int):
        self.__events = events

    def set_slot(self, slot: int):
        self.__slot = slot

    def set_scalereweight(self, minID: int):
        self.__reweightscale = True
        self.__minid = minID

    def set_pdfreweight(self, minpdf:int, maxpdf:int, minID: int):
        self.__reweightpdf = True
        self.__minpdf = minpdf
        self.__maxpdf = maxpdf
        self.__minid = minID

    def set_parallelstage(self, stage: int, xgriditer: int):
        self.__stage = stage
        self.__xgriditer = xgriditer

    def set_gridrepository(self, gridrepository: str):
        self.__gridrepository = gridrepository

    def set_powhegtype(self, pwhgtype):
        if not is_valid_process(pwhgtype):
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

    def get_slot(self) -> int:
        return self.__slot

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

    def is_parallelstage(self) -> bool:
        return self.__stage > 0

    def get_stage_level(self) -> int:
        return self.__stage
    
    def get_xgriditer(self) -> int:
        return self.__xgriditer

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
        if not self.is_reweight() and not self.is_parallelstage():
            if self.__workdir_has_pwgevents():
                found_semaphore = has_semaphore(self.workdir)
                if found_semaphore:
                    logging.warning("Existing pwgevents.lhe in directory %s incomplete - reprocessing ...", self.workdir)
                    found_semaphore.remove()
                    os.remove()
                else:
                    logging.error("pwgevents.lhe (complete) already found in working directory %s for non-reweight jon - cannot run ...", self.workdir)
                    return False
            logging.info("Running standard powheg job")
            self.__run_powhegjob("pwhg.log")
        elif self.is_parallelstage():
            self.__run_stage_job()
        else:
            if self.is_scalereweight():
                self.__run_scalereweight()
            elif self.__run_pdfreweight():
                self.__run_pdfreweight()
        self.__pack_grids()
        return True

    def __run_scalereweight(self):
        os.chdir(self.__workdir)
        currentid = self.__minid
        currentpwgevents = pwgevents_info()
        variations = [0.5, 1., 2.]
        for indexMuR in range(0, 3):
            variationMuR = variations[indexMuR]
            for indexMuF in range(0, 3):
                variationMuF = variations[indexMuF]
                self.__list_workdir()
                if self.__workdir_has_reweightevents():
                    logging.error("pwgevents-reweight.lhe found in workdir %s in weighting mode, removing ...", self.__workdir)
                    os.remove(os.path.join(self.workdir, "pwgevents-reweight.lhe"))
                if indexMuR == 1 and indexMuF == 1:
                    logging.info("Skipping default variation muf = mur = 1")
                    continue
                if self.__workdir_has_pwgevents():
                    currentpwgevents = self.__decode_pwgfile(os.path.join(self.workdir, "pwgevents.lhe"))
                foundweight = currentpwgevents.find_weight("{}".format(currentid))
                if foundweight:
                    logging.info("Scale variation  mur = %f, muf = %f with weight ID %d already existing, not running again ...", variationMuR, variationMuF, currentid)
                    currentid += 1
                    continue 
                logging.info("Running variation mur = %f, muf = %f", variationMuR, variationMuF)
                currentWeightID = build_weightID_scalereweight(variationMuF, variationMuR, currentid)
                if currentWeightID in self.__foundweights:
                    logging.info("Weight ID %s (%s) already found - not running again", currentWeightID.name, currentWeightID.title)
                    continue
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
        currentpwgevents = pwgevents_info()
        while currentpdf <= self.__maxpdf:
            self.__list_workdir()
            if self.__workdir_has_reweightevents():
                logging.error("pwgevents-reweight.lhe found in workdir %s in weighting mode, removing ...", self.__workdir)
                os.remove(os.path.join(self.workdir, "pwgevents-reweight.lhe"))
            if self.__workdir_has_pwgevents():
                currentpwgevents = self.__decode_pwgfile(os.path.join(self.workdir, "pwgevents.lhe"))
            foundweight = currentpwgevents.find_weight("{}".format(currentid))
            if foundweight:
                logging.info("PDF variation %d with weight ID %d already existing, not running again ...", currentpdf, currentid)
                currentid += 1
                currentpdf += 1
                continue
            logging.info("Running pdf variation %d with weight ID %d", currentpdf, currentid)
            currentWeightID = build_weightID_pdfreweight(currentpdf, currentid)
            if currentWeightID in self.__foundweights:
                logging.info("Weight ID %s (%s) already found - not running again", currentWeightID.name, currentWeightID.title)
                continue
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
        semaphore = pwsemaphore(self.__workdir)
        semaphore.create()
        subprocess.call(command, shell=True)
        semaphore.remove()

    def __run_stage_job(self):
        os.chdir(self.__workdir)
        logfile = os.path.join(os.getcwd(), "logs", f"runpowheg_stage{self.__stage}")
        if self.__stage == 1:
            logfile += f"_xgriditer{self.__xgriditer}"
        logfile += f"_{self.__slot}.log"
        command = f"pwhg_main_{self.__powhegtype} << EOF\n"
        command += f"{self.__slot}\n"
        command += f"EOF"
        with open(logfile, "w") as logwriter:
            subprocess.call(command, shell=True, stdout=logwriter, stderr=subprocess.STDOUT)
            logwriter.close()

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

    def __decode_pwgfile(self, pwgfile: str) -> pwgevents_info:
        decoder = pwgeventsparser(pwgfile)
        decoder.parse()
        return decoder.get_eventinfos()

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

    def __pack_grids(self):
        if self.__gridarchive:
            if not self.__workdir_has_file("grids.zip"):
                self.__gridarchive.build("grids.zip")
            self.__gridarchive.clean_gridfiles(self.__workdir)

    def __extractgrids(self, gridarchivefile: str):
        if self.__gridarchive:
            wd = os.getcwd()
            os.chdir(self.__workdir)
            self.__gridarchive.extract(gridarchivefile)
            os.chdir(wd)

    def __prepare_workdir(self):
        if self.is_parallelstage():
            # Workdir handled outside in parallelstage
            self.__workdirInitialized = True
            return
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
            if self.__workdir_has_powheginput():
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
            if not self.__gridrepository.endswith(".zip"):
                self.__gridarchive = init_archive(self.__gridrepository)
                self.__gridarchive.stage(self.__gridrepository, self.__workdir)
            else:
                self.__gridarchive = gridarchive()
                self.__extractgrids(self.__gridrepository)
            if not self.__gridarchive.check():
                logging.error("Request running with existing grids, but not all expected files found, cannot run ...")
                return
            logging.info("Found %d grid files in %s (%s mode)", self.__gridarchive.number_allgrids(), self.__gridrepository, "parallel" if self.__gridarchive.is_parallel_mode() else "sequential") 
        else:
            localgrids = os.path.join(self.__workdir, "grids.zip")
            if os.path.exists(localgrids):
                self.__gridarchive = gridarchive()
                self.__extractgrids(localgrids)
                if not self.__gridarchive.check():
                    logging.error("Request running with existing grids, but not all expected files found, cannot run ...")
                    return
                logging.info("Found %d grid files in grids.zip in working directory (%s mode)", self.__gridarchive.number_allgrids(), "parallel" if self.__gridarchive.is_parallel_mode() else "sequential") 
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
    parser.add_argument("--slotoffset", metavar="SLOTOFFSET", type=int, default=0, help="Offset in slot index")
    parser.add_argument("--stage", metavar="STAGE", type=int, default=0, help="Parallel stage")
    parser.add_argument("--xgriditer", metavar="XGRIDITER", type=int, default=1, help="xgrid iteration (parallel stage 1)")
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
    if slot < 0:
        # try to find slot index from environment variable "SLOT"
        envslot = os.getenv("SLOT")
        if envslot:
            slot = int(envslot)
            slot += args.slotoffset 
            if args.stage == 0:
                # do not add slot in case of parallelstage
                workdir = os.path.join(workdir, "%04d" %slot)
            workdirmessage = f"Using working directory: {workdir} (slot {slot})"
        else:
            workdirmessage = f"Using working directory: {workdir} (sequential mode)"
    logging.info(workdirmessage)

    processor = POWHEG_runner(workdir, os.path.abspath(args.input))
    processor.set_powhegtype(args.type)
    processor.set_slot(slot)
    if scalereweight:
        processor.set_scalereweight(args.minid)
    if pdfreweight:
        processor.set_pdfreweight(args.minpdf, args.maxpdf, args.minid)
    if len(args.gridfiledir):
        processor.set_gridrepository(os.path.abspath(args.gridfiledir))
    if args.events > 0:
        processor.set_events(args.events)
    if args.stage > 0 and args.stage < 4:
        processor.set_parallelstage(args.stage, args.xgriditer)
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