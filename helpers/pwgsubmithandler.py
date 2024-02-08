#! /usr/bin/env python3

import logging
import os

from helpers.containerwrapper import create_containerwrapper
from helpers.cluster import get_default_partition
from helpers.modules import get_OSVersion
from helpers.powhegconfig import get_energy_from_config
from helpers.simconfig import SimConfig
from helpers.slurm import submit_range, SlurmConfig

class UninitException(Exception):

    def __init__(self, type: str):
        self.__type = type

    def __str__(self):
        return f"{self.__type} not initialized"

class PowhegSubmitHandler(object):

    def __init__(self):
        self.__repo = ""
        self.__simconfig: SimConfig = None
        self.__batchconfig: SlurmConfig = None
        self.__singleslot = False

    def set_repo(self, repo: str):
        self.__repo = repo

    def set_simconfig(self, config: SimConfig):
        self.__simconfig = config

    def set_batchconfig(self, config: SlurmConfig):
        self.__batchconfig = config

    def set_singleslot(self, singleslot: bool):
        self.__singleslot = singleslot
    
    def submit(self) ->int:
        if not len(self.__repo):
            raise UninitException("Repository")
        if not self.__simconfig:
            raise UninitException("SimParams")
        if not self.__batchconfig:
            raise UninitException("BatchConfig")
        logging.info("Submitting POWHEG release %s", self.__simconfig.powhegversion)
        powheg_version_string = self.__simconfig.powhegversion
        if "VO_ALICE@POWHEG::" in powheg_version_string:
            powheg_version_string = powheg_version_string.replace("VO_ALICE@POWHEG::", "")
        workdir= os.path.join(self.__simconfig.workdir, f"POWHEG_{powheg_version_string}")
        logdir = os.path.join(workdir, "logs")
        if not os.path.exists(logdir):
            os.makedirs(logdir, 0o755)
        logfile = ""
        if self.__singleslot:
            logfile = os.path.join(logdir, f"joboutput{self.__simconfig.minslot}.log")
        else:
            logfile = os.path.join(logdir, "joboutput%a.log")
        energytag = "%.1fT" %(get_energy_from_config(self.__simconfig.powheginput)/1000) if self.__simconfig.powheginput else "None"
        logging.info("Running simulation for energy %s", energytag)
        runcmd =  "%s %s" %(self.__configure_env(), self.__make_powhegrunner())
        #executable = os.path.join(repo, "run_powheg_singularity.sh")
        #f"{executable} {batchconfig.cluster} {repo} {workdir} {simconfig.process} {simconfig.powhegversion} {simconfig.powheginput} {simconfig.minslot} {simconfig.gridrepository} {simconfig.nevents}"
        jobname = f"pp_{self.__simconfig.process}_{energytag}"
        if self.__batchconfig.cluster == "CADES" or self.__batchconfig.cluster == "PERLMUTTER":
            runcmd = "%s %s" %(create_containerwrapper(workdir, self.__batchconfig.cluster, get_OSVersion(self.__batchconfig.cluster, self.__simconfig.powhegversion)), runcmd)
        elif self.__batchconfig.cluster == "B587" and "VO_ALICE" in self.___simconfig.powhegversion:
            # needs container also on the 587 cluster for POWHEG versions from cvmfs
            # will use the container from ALICE, so the OS version does not really matter
            runcmd = "%s %s" %(create_containerwrapper(workdir, self.__batchconfig.cluster, "CentOS8"), runcmd)
        logging.debug("Running on hosts: %s", runcmd)
        return submit_range(runcmd, self.__batchconfig.cluster, jobname, logfile, get_default_partition(self.__batchconfig.cluster) if self.__batchconfig.partition == "default" else self.__batchconfig.partition, {"first": 0, "last": self.__batchconfig.njobs-1}, "{}:00:00".format(self.__batchconfig.hours), "{}G".format(self.__batchconfig.memory))

    def __make_powhegrunner(self) -> str:
        executable = f"{self.__repo}/powheg_runner.py"
        workdir = os.path.join(self.__simconfig.workdir, f"POWHEG_{self.__simconfig.powhegversion}")
        cmd = f"{executable} {workdir} -t {self.__simconfig.process}"
        if not self.__simconfig.is_scalereweight() and not self.__simconfig.is_pdfreweight():
            cmd += f" -i {self.__simconfig.powheginput}"
            if self.__simconfig.nevents > 0:
                cmd += f" -e {self.__simconfig.nevents}"
        if self.__simconfig.minslot > 0:
            cmd += f" --slotoffset {self.__simconfig.minslot}"
        if len(self.__simconfig.gridrepository) and self.__simconfig.gridrepository != "NONE":
            cmd += f" -g {self.__simconfig.gridrepository}"
        if self.__simconfig.is_scalereweight():
            cmd += " -s --minid 0"
        if self.__simconfig.is_pdfreweight():
            cmd += f" --minpdf {self.__simconfig.minpdf} --maxpdf {self.__simconfig.maxpdf} --minid {self.__simconfig.minID}"
        logging.debug("Running POWHEG command: %s", cmd)
        return cmd

    def __configure_env(self) -> str:
        executable = f"{self.__repo}/powheg_run_in_env.sh"
        return f"{executable} {self.__repo} {self.__batchconfig.cluster} {self.__simconfig.powhegversion}"

def submit_simulation(repo: str, simconfig: SimConfig, batchconfig: SlurmConfig, singleslot: bool = False) -> int:
    executor = PowhegSubmitHandler()
    executor.set_repo(repo)
    executor.set_simconfig(simconfig)
    executor.set_batchconfig(batchconfig)
    executor.set_singleslot(singleslot)
    return executor.submit()