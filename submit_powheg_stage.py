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
        self.__workdir = workdir
        self.__stage = stage
        self.__xgriditer = xgriditer
        self.__slots = slots
        self.__config = config
        self.__jobid = -1
        self.__originalInput = ""
        self.__nextsubmitter = -1

    def build_stage(self, pwginput: str, nevents: int):
        if not os.path.exists(self.__workdir):
            os.makedirs(self.__workdir, 0o755)
        build_powheg_stage(pwginput, self.__workdir, self.__stage, self.__xgriditer, self.__slots, nevents)
        build_powhegseeds(self.__workdir, self.__slots)
        self.__originalInput = pwginput

    def get_jobid(self) -> int:
        return self.__jobid

    def get_jobid_nextstage(self) ->int:
        return self.__nextsubmitter

    def __build_command(self, powheg_version: str)-> str:
        return f"{self.__executable} {self.__config.cluster()} {repo} {self.__workdir} {powheg_version} {self.__stage} {self.__xgriditer}"

    def submit(self, powheg_version):
        jobname = "pwg_st{}".format(self.__stage)
        logfilebase =  "powheg_stage{}".format(self.__stage)
        if self.__stage == 1:
            jobname += "_xg{}".format(self.__xgriditer)
            logfilebase += "_xgriditer{}".format(self.__xgriditer)
        logfilebase += "_%a.log"
        logdir = os.path.join(self.__workdir, "logs")
        if not os.path.exists(logdir):
            os.makedirs(logdir, 0o755)
        logfile = os.path.join(logdir, logfilebase)
        self.__jobid = submit(self.__build_command(powheg_version), self.__config.cluster(), jobname, logfile, self.__config.queue(), self.__slots, self.__config.timelimit(), self.__config.memory())
    
    def submit_next(self, powheg_version):
        if self.__stage == 3:
            logging.info("Already at the last stage, no more stages to submit")
            return
        nextstage = 1
        nextiter = 2
        if self.__stage == 1:
            if self.__xgriditer == 1:
                nextiter = griditer = 2
            else:
                nextstage = 2
                nextiter = 1
        elif self.__stage == 2:
            nextstage = 3
        logfilename = f"submit_stage{nextstage}"
        jobname = f"submit_stage{nextstage}"
        # remove powheg version from workdir
        stripped_workdir = self.__workdir
        stripped_workdir = stripped_workdir.replace(f"POWHEG_{powheg_version}", "")
        stripped_workdir = stripped_workdir.rstrip("/")
        runcmd = f"{repo}/stagewrapper.sh {repo}/submit_powheg_stage.py {stripped_workdir} --repo {repo} -i {self.__originalInput} -n {self.__slots} -v {powheg_version} -p {self.__config.queue()} -s {nextstage}"
        if nextstage == 1:
            runcmd = f"{runcmd} -x {nextiter}"
            jobname = f"{jobname}_xgrid{nextiter}"
            logfilename = f"{logfilename}_xgrid{nextiter}"
        logfilename = f"{logfilename}.log"
        memory_int = self.__config.memory().split("G")[0]
        hours = self.__config.timelimit().split(":")[0]
        runcmd = f"{runcmd} --mem {memory_int} --hours {hours} -c"
        logfile = os.path.join(self.__workdir, "logs", logfilename)
        self.__nextsubmitter = submit(runcmd, self.__config.cluster(), jobname, logfile, self.__config.queue(), 0, "00:30:00", "2G", self.__jobid)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg_stage.py", description="Submitter for multi-stage POWHEG")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=200, help="Number of slots")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=25000, help="Number of events (stage4)")
    parser.add_argument("-m", "--minslot", metavar="MINSLOT", type=int, default=0, help="Min. slot ID")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="r3898", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-s", "--stage", metavar="STAGE", type=int, default=1, help="POWHEG parallel stage (default: 1)")
    parser.add_argument("-x", "--xgrid", metavar="XGRID", type=int, default=1, help="POWHEG parallel stage (default: 1)")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-c", "--continuestage", action="store_true", help="automatically submit next stage")
    parser.add_argument("--repo", metavar="REPO", type=str, default="", help="Repository")
    args = parser.parse_args()
    setup_logging(args.debug)

    if len(args.repo):
        # Mainly needed for automatic submission of higher stages
        repo = args.repo

    if args.stage > 4:
        logging.error("Max. 4 stages")
        sys.exit(1)

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
    job = MultiStageJob(workdir, args.stage, args.xgrid, args.njobs, config)
    job.build_stage(args.input, args.events)
    job.submit(args.version)
    logging.info("Submitted stage job under ID %d", job.get_jobid())
    if args.continuestage:
        job.submit_next(args.version)
        submitter_next = job.get_jobid_nextstage()
        if submitter_next > -1:
            logging.info("Launched sumbitter for next stage/xgrid under ID %d", submitter_next)