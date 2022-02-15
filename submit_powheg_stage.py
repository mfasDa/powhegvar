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
        self.__timelimit == timelimit

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

    def build_stage(self, pwginput: str, nevents: int):
        if not os.path.exists(self.__workdir):
            os.makedirs(self.__workdir, 0o755)
        build_powheg_stage(pwginput, self.__workdir, self.__stage, self.__xgriditer, self.__slots, nevents)
        build_powhegseeds(self.__workdir, self.__slots)

    def get_jobid(self) -> int:
        return self.__jobid

    def __build_command(self, powheg_version: str)-> str:
        return "{EXE} {CLUST} {REPO} {WD} {VERSION} {STAGE} {ITER}".format(EXE=self.__executable, CLUST=self.__config.cluster(), REPO=repo, WD=self.__workdir, VERSION=powheg_version, STAGE=self.__stage, ITER=self.__xgriditer)

    def submit(self, powheg_version):
        jobname = "pwg_st{}".format(self.__stage)
        logfilenbase =  "powheg_stage{}".format(self.__stage)
        if self.__stage == 1:
            jobname += "_xg{}".format(self.__xgriditer)
            logfilenbase += "xgriditer{}"
        logfilebase += "_%a.log"
        logdir = os.path.join(self.workdir, "logs")
        if not os.path.exists(logdir):
            os.makedirs(logdir, 0o755)
        logfile = os.path.join(logdir, logfilenbase)
        self.__jobid = submit(self.__build_command(powheg_version), self.__config.cluster(), jobname, logfile, self.__config.queue(), self.__slots, self.__config.timelimit(), self.__config.memory())

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg_stage.py", description="Submitter for multi-stage POWHEG")
    args = parser.parse_args()
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
    args = parser.parse_args()
    setup_logging(args.debug)

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
    config = slurmconfig(partition, timelimit, memory)

    workdir = os.path.join(args.workdir, "POWHEG_{}".format(args.version))
    job = MultiStageJob(workdir, args.stage, args.xgrid, args.njobs, config)
    job.build_stage(args.input, args.events)
    job.submit(args.version)
    logging.info("Submitted stage job under ID %d", job.get_jobid())