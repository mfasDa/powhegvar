#! /usr/bin/env python3

import logging
import subprocess

class SlurmConfig:

    def __init__(self):
        self.__cluster = ""
        self.__partition = ""
        self.__jobame = ""
        self.__logfile = ""
        self.__environment = ""
        self.__cpus = 1
        self.__njobs = 1
        self.__dependency = -1
        self.__hours = 10
        self.__memory = 4

    def set_cluster(self, cluster: str):
        self.__cluster = cluster

    def set_partition(self, partition: str):
        self.__partition = partition

    def set_jobname(self, jobname: str):
        self.__jobame = jobname

    def set_logfile(self, logfile: str):
        self.__logfile = logfile

    def set_environment(self, environment: str):
        self.__environment = environment

    def set_njobs(self, njobs: int):
        self.__njobs = njobs

    def set_cpus(self, cpus: int):
        self.__cpus = cpus

    def set_dependency(self, dependency: int):
        self.__dependency = dependency

    def set_hours(self, hours: int):
        self.__hours = hours

    def set_memory(self, memory: int):
        self.__memory = memory

    def get_cluster(self) -> str:
        return self.__cluster

    def get_partition(self) -> str:
        return self.__partition

    def get_jobame(self) -> str:
        return self.__jobame

    def get_logfile(self) -> str:
        return self.__logfile

    def get_environment(self) -> str:
        return self.__environment 

    def get_njobs(self) -> int:
        return self.__njobs

    def get_cpus(self) -> int:
        return self.__cpus

    def get_dependency(self) -> int:
        return self.__dependency

    def get_hours(self) -> int:
        return self.__hours

    def get_memory(self) -> int:
        return self.__memory
    
    cluster = property(fget=get_cluster, fset=set_cluster)
    partition = property(fget=get_partition, fset=set_partition)
    jobname = property(fget=get_jobame, fset=set_jobname)
    logfile = property(fget=get_logfile, fset=set_logfile)
    environment = property(fget=get_environment, fset=set_environment)
    dependency = property(fget=get_dependency, fset=set_dependency)
    njobs = property(fget=get_njobs, fset=set_njobs)
    cpus = property(fget=get_cpus, fset=set_cpus)
    hours = property(fget=get_hours, fset=set_hours)
    memory = property(fget=get_memory, fset=set_memory)


class SlurmJob:

    def __init__(self, runcmd: str = "",  batchconfig: SlurmConfig = None):
        self.__runcmd = runcmd
        self.__batchconfig = SlurmConfig() if not batchconfig else batchconfig
        self.__jobid = -1

    def set_runcmd(self, runcmd: str):
        self.__runcmd = runcmd

    def set_config(self, config: SlurmConfig):
        self.__batchconfig = config

    def get_runcmd(self) -> int:
        return self.__runcmd

    def get_config(self) -> SlurmConfig:
        return self.__batchconfig

    def get_jobid(self) -> int:
        return self.__jobid

    def is_submitted(self) -> bool:
        return self.__jobid > -1

    def __configure_slurm(self) -> str:
        logging.info("Using logfile: %s", self.__batchconfig.logfile)
        submitcmd = "sbatch "
        if self.__batchconfig.cluster == "CADES":
            submitcmd += " -A birthright" 
        submitcmd += " -N 1 -n 1 -c {}".format(self.__batchconfig.cpus)
        if self.__batchconfig.cluster == "PERLMUTTER":
            submitcmd += " --qos={}".format(self.__batchconfig.partition)
        else:
            submitcmd += " --partition {}".format(self.__batchconfig.partition)
        submitcmd += " -J {}".format(self.__batchconfig.jobname)
        submitcmd += " -o {}".format(self.__batchconfig.logfile)
        if self.__batchconfig.cluster == "CADES" or self.__batchconfig.cluster == "PERLMUTTER":
            submitcmd += " --time={:02d}:00:00".format(self.__batchconfig.hours)
            submitcmd += " --mem={}G".format(self.__batchconfig.memory)
        if self.__batchconfig.dependency > -1:
            submitcmd += " -d {}".format(self.__batchconfig.dependency)
        if len(self.__batchconfig.environment):
            submitcmd += "export={}".format(self.__batchconfig.environment)
        if self.__batchconfig.cluster == "PERLMUTTER":
            submitcmd += " --constraint=cpu"
            submitcmd += " --licenses=cvmfs,cfs"
            submitcmd += " --image=docker:mfasel/cc8-alice:latest"
        if self.__batchconfig.njobs > 1:
            submitcmd += " --array=0-{}".format(self.__batchconfig.njobs-1)
        return submitcmd

    def submit(self):
        submitcmd = self.__configure_slurm()
        submitcmd += " {}".format(self.__runcmd)
        logging.debug(submitcmd)
        submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
        sout = submitResult.stdout.decode("utf-8")
        toks = sout.split(" ")
        self.__jobid = int(toks[len(toks)-1])

    runcmd = property(fget=get_runcmd, fset=set_runcmd)
    config = property(fget=get_config, fset=set_config)

def ncorejob(cluster: str, cpus: int, jobname: str, logfile: str, partition: str, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1, environment: str = "") -> str:
    logging.info("Using logfile: %s", logfile)
    submitcmd = "sbatch "
    if cluster == "CADES":
        submitcmd += " -A birthright" 
    submitcmd += " -N 1 -n 1 -c {}".format(cpus)
    if cluster == "PERLMUTTER":
        submitcmd += " --qos={}".format(partition)
    else:
        submitcmd += " --partition {}".format(partition)
    submitcmd += " -J {}".format(jobname)
    submitcmd += " -o {}".format(logfile)
    if cluster == "CADES" or cluster == "PERLMUTTER":
        submitcmd += " --time={}".format(timelimit)
        submitcmd += " --mem={}".format(memory)
    if dependency > -1:
        submitcmd += " -d {}".format(dependency)
    if len(environment):
        submitcmd += "export={}".format(environment)
    if cluster == "PERLMUTTER":
        submitcmd += " --constraint=cpu"
        submitcmd += " --licenses=cvmfs,cfs"
        submitcmd += " --image=docker:mfasel/cc8-alice:latest"
    return submitcmd

def submit(command: str, cluster: str, jobname: str, logfile: str, partition: str, arraysize: int = 0, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1, envrionment: str = "") -> int:
    submitcmd = ncorejob(cluster, 1, jobname, logfile, partition, timelimit, memory, dependency)
    if arraysize > 0:
        submitcmd += " --array=0-{}".format(arraysize-1)
    submitcmd += " {}".format(command)
    logging.debug(submitcmd)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid

def submit_range(command: str, cluster: str, jobname: str, logfile: str, partition: str, arrayrange: dict, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1, nevironment: str = "") -> int:
    submitcmd = ncorejob(cluster, 1, jobname, logfile, partition, timelimit, memory, dependency)
    submitcmd += " --array={}-{}".format(arrayrange["first"], arrayrange["last"])
    submitcmd += " {}".format(command)
    logging.debug(submitcmd)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid