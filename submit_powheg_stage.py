#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from helpers.setup_logging import setup_logging
from helpers.slurm import submit
from helpers.powheg import build_powheg_stage, build_powhegseeds
from helpers.cluster import get_cluster, get_default_partition
from helpers.modules import find_powheg_releases

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

class slurmconfig:

    def __init__(self, cluster: str, queue: str, timelimit: str, memory: str):
        self.__cluster = cluster
        self.__queue = queue
        self.__memory = memory
        self.__timelimit = timelimit

    def cluster(self) ->str:
        return self.__cluster
    
    def queue(self) -> str:
        return self.__queue

    def memory(self) -> str:
        return self.__memory

    def timelimit(self) -> str:
        return self.__timelimit

class MultiStageJob:
    def __init__(self, workdir: str, stage: int, xgriditer: int, slots: int, config: slurmconfig):
        self.__executable = os.path.join(repo, "powheg_stage_steer.sh")
        self.__prepare_executable = os.path.join(repo, "powheg_stage_prepare.sh")
        self.__workdir = workdir
        self.__stage = stage
        self.__xgriditer = xgriditer
        self.__slots = slots
        self.__config = config
        self.__jobid = -1
        self.__jobidPrepare = -1
        self.__dependency = -1
        self.__stageconfig = "default"
        self.__stageseeds = "default"

    def set_dependency(self, dependency: int):
        self.__dependency = dependency

    def build_stage(self, pwginput: str, nevents: int) -> tuple: 
        if not os.path.exists(self.__workdir):
            os.makedirs(self.__workdir, 0o755)
        self.__stageconfig = os.path.join(self.__workdir, f"powheg_stage{self.__stage}_xgiter{self.__xgriditer}.input")
        self.__stageseeds = os.path.join(self.__workdir, f"pwgseeds_stage{self.__stage}_xgiter{self.__xgriditer}.input")
        build_powheg_stage(pwginput, self.__workdir, self.__stage, self.__xgriditer, self.__slots, nevents, self.__stageconfig)
        build_powhegseeds(self.__workdir, self.__slots, self.__stageseeds)

    def get_jobid(self) -> int:
        return self.__jobid
    
    def get_jobid_prepare(self) -> int:
        return self.__jobidPrepare

    def __build_command(self, powheg_version: str)-> str:
        return f"{self.__executable} {self.__config.cluster()} {repo} {self.__workdir} {powheg_version} {self.__stage} {self.__xgriditer}"

    def __prepare_command(self):
        return f"{self.__prepare_executable} {self.__workdir} {self.__stageconfig} {self.__stageseeds}"

    def submit(self, powheg_version, timelimit = ""):
        jobname = f"pwg_st{self.__stage}"
        jobname_prepare = f"pwprep_st{self.__stage}"
        logfilebase =  f"powheg_stage{self.__stage}"
        logfilebase_prepare = f"powhegprep_stage{self.__stage}"
        if self.__stage == 1:
            jobname += f"_xg{self.__xgriditer}"
            jobname_prepare += f"_xg{self.__xgriditer}"
            logfilebase += f"_xgriditer{self.__xgriditer}"
            logfilebase_prepare += f"_xgriditer{self.__xgriditer}"
        logfilebase += "_%a.log"
        logdir = os.path.join(self.__workdir, "logs")
        if not os.path.exists(logdir):
            os.makedirs(logdir, 0o755)
        logfile = os.path.join(logdir, logfilebase)
        logfile_prepare = os.path.join(logdir, logfilebase_prepare)
        if len(timelimit):
            timelimit =  self.__config.timelimit()
        self.__jobidPrepare = submit(self.__prepare_command(), self.__config.cluster(), jobname_prepare, logfile_prepare, self.__config.queue(), 1, "00:10:00", "2G", self.__dependency)
        self.__jobid = submit(self.__build_command(powheg_version), self.__config.cluster(), jobname, logfile, self.__config.queue(), self.__slots, timelimit, self.__config.memory(), self.__jobidPrepare)
    
class StageConfiguration:

    class StageException(Exception):

        def __init__(self, stageIndex: int):
            super(self, Exception).__init__()
            self.__stageIndex = stageIndex

        def __str__(self): 
            return f"Stage index {self.__stageIndex} not existing"

        def get_stageindex(self) -> int:
            return self.__stageIndex

    class Stage:
        def __init__(self, stageindex: int, xgindex: int, timelimeit: str):
            self.__stageindex = stageindex
            self.__xgindex = xgindex
            self.__timelimit = timelimeit

        def set_stageindex(self, stageindex: int):
            self.__stageindex = stageindex

        def set_xgindex(self, xgindex: int):
            self.__xgindex = xgindex

        def set_timelimit(self, timelimit: str):
            self.__timelimit = timelimit

        def get_stageindex(self) -> int:
            return self.__stageindex
        
        def get_xgindex(self) -> int:
            return self.__xgindex
        
        def get_timelimit(self) -> int:
            return self.__timelimit

        stageindex = property(fset=set_stageindex, fget=get_stageindex)
        xgindex = property(fset=set_xgindex, fget=get_xgindex)
        timelimit = property(fset=set_timelimit, fget=get_timelimit)

    def __init__(self):
        self.__currentstage = 0
        self.__configs = []
        self.__built_config()

    def __built_config(self):
        self.__configs.clear()
        self.__configs.append(self.Stage(1, 1, "00:30:00"))
        self.__configs.append(self.Stage(1, 2, "00:30:00"))
        self.__configs.append(self.Stage(2, 1, "00:05:00"))
        self.__configs.append(self.Stage(3, 1, "00:05:00"))

    def get_current_stage(self) ->Stage:
        if self.__currentstage >= len(self.__configs):
            raise self.StageException(self.__currentstage)
        return self.__configs[self.__currentstage]

    def hasNextStage(self):
        return self.__currentstage + 1 < len(self.__configs)

    def get_next_stage(self) -> Stage:
        self.forward_stage()
        return self.__configs[self.__currentstage]
    
    def forward_stage(self):
        if self.__currentstage + 1 >= len(self.__configs):
           raise self.StageException(self.__currentstage + 1) 
        self.__currentstage += 1 


class StageHandler:

    def __init__(self, workdir: str, powheginput: str, pwgversion: int, njobs: int, batchconfig):
        self.__workdir = workdir
        self.__pwginput = powheginput
        self.__pwgversion = pwgversion
        self.__njobs = njobs
        self.__batchconfig = batchconfig
        self.__stageconfig = StageConfiguration()

    def submit_stage(self, config: StageConfiguration.Stage, dependency: int = -1) -> int:
        jobdef = MultiStageJob(self.__workdir, config.stageindex, config.xgindex, self.__njobs, self.__batchconfig)
        if dependency >= 0:
            jobdef.set_dependency(dependency)
        jobdef.build_stage(self.__pwginput, 1)
        jobdef.submit(self.__pwgversion, config.timelimit)
        jobid = jobdef.get_jobid()
        jobid_prepare = jobdef.get_jobid_prepare()
        logging.info("Submitting Stage %d, xgrid iteration %d under Job ID %d (prepare Job ID %d)", config.stageindex, config.xgindex, jobid, jobid_prepare)
        return jobid

    def process(self):
        currentJob = self.submit_stage(self.__stageconfig.get_current_stage())
        while self.__stageconfig.hasNextStage():
            currentJob = self.submit_stage(self.__stageconfig.get_next_stage(), currentJob)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg_stage.py", description="Submitter for multi-stage POWHEG")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=200, help="Number of slots")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="r3898", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("--repo", metavar="REPO", type=str, default="", help="Repository")
    args = parser.parse_args()
    setup_logging(args.debug)

    if len(args.repo):
        # Mainly needed for automatic submission of higher stages
        repo = args.repo

    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    if cluster == "CADES":
       if not args.version in find_powheg_releases():
           logging.error("Requested POWHEG release not available on cluster %s", cluster)
           sys.exit(1)

    timelimit = "{}:00:00".format(args.hours)
    memory = "{}G".format(args.mem)
    config = slurmconfig(cluster, partition, timelimit, memory)

    workdir = os.path.join(args.workdir, "POWHEG_{}".format(args.version))
    submitter = StageHandler(workdir, args.input, args.version, args.njobs, config)
    submitter.process()