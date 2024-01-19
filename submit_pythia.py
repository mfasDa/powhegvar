#! /usr/bin/env python3

import argparse
import logging
import os
import sys
from helpers.cluster import get_cluster, get_default_partition, get_fast_partition
from helpers.containerwrapper import create_containerwrapper
from helpers.datahandler import find_pwgevents
from helpers.modules import find_pythiaversion, get_pythia_OSVersion
from helpers.pythiaparams import PythiaParams
from helpers.setup_logging import setup_logging
from helpers.slurm import submit

repo = os.path.abspath(os.path.dirname(sys.argv[0]))

class Filelist :

    def __init__(self, name: str):
        self.__name = name
        self.__files = []

    def add_file(self, filename: str):
        self.__files.append(filename)

    def size(self):
        return len(self.__files)

    def build(self):
        with open(self.__name, "w") as filewriter:
            for fl in self.__files:
                filewriter.write("{}\n".format(fl))
            filewriter.close()

def split(filelistdir: str, pwhgfiles: list, chunksize: int) -> list:
    if not os.path.exists(filelistdir):
        os.makedirs(filelistdir, 0o755)
    filelists = []
    currentfile = Filelist(os.path.join(filelistdir, "pwhgin{}.txt".format(len(filelists))))
    for file in pwhgfiles:
        currentfile.add_file(file)
        if currentfile.size() == chunksize:
            filelists.append(currentfile)
            currentfile = Filelist(os.path.join(filelistdir, "pwhgin{}.txt".format(len(filelists))))
    if currentfile.size() != 0:
        filelists.append(currentfile)

    for flist in filelists:
        flist.build()
	
    return filelists

def build_logfile(logfile: str):
    logdir = os.path.dirname(logfile)
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    return logfile

def configure_env(cluster: str, pythiaversion: str) -> str:
    executable = f"{repo}/pythia_run_in_env.sh"
    return f"{executable} {repo} {cluster} {pythiaversion}"

def submit_clean(cluster: str, outputbase: str, partition: str, dependency: int) -> int:
    script = os.path.join(repo, "pythia_clean.sh")
    command = "{} {}".format(script, outputbase)
    logfile = build_logfile(os.path.join(outputbase, "logs", "clean.log"))
    return submit(command, cluster, "clean_py", logfile, partition, 0, "00:10:00", "2G", [dependency])

def submit_merge(cluster: str, outputbase: str, rootfile: str, partition: str, dependency: int):
    script = os.path.join(repo, "pythia_merge.sh")
    command = "{} {} {} {} {}".format(script, cluster, repo, outputbase, rootfile)
    logfile = build_logfile(os.path.join(outputbase, "logs", "merge.log"))
    return submit(command, cluster, "merge_py", logfile, partition, 0, "01:00:00", "4G", [dependency]) 

def submit_pythia(cluster: str, outputdir: str, inputdir: str, chunksize: int, pythiaver: str, macro: str, pythiasettings: PythiaParams, partition: str, timelimit: str = "10:00:00") -> int:
    files = find_pwgevents(inputdir)
    logging.info("Found %d files", len(files))
    filelists = split(os.path.join(outputdir, "filelists"), files, chunksize)
    logging.info("Submitting %d PYTHIA jobs", len(filelists))
    script = os.path.join(repo, "pythia_runner.py")
    pythia_command = f"{script} {outputdir} slotfilelist {macro}"
    pythia_command += " -c \"{}\"".format(pythiasettings.serialize())
    runcmd = "{} {}".format(configure_env(cluster, pythiaver), pythia_command)
    if cluster == "CADES" or cluster == "PERLMUTTER":
        runcmd = "%s %s" %(create_containerwrapper(outputdir, cluster, get_pythia_OSVersion(cluster, pythiaver)), runcmd)
    elif cluster == "B587" and "VO_ALICE" in pythiaver:
        # needs container also on the 587 cluster for POWHEG versions from cvmfs
        # will use the container from ALICE, so the OS version does not really matter
        runcmd = "%s %s" %(create_containerwrapper(outputdir, cluster, "CentOS8"), runcmd)
    logfile = build_logfile(os.path.join(outputdir, "logs", "pythia%a.log"))
    jobname = f"py_{pythiaver}"
    logging.debug("Submitting run command: %s", runcmd)
    return submit(runcmd, cluster, jobname, logfile, partition, len(filelists), timelimit)

if __name__ == "__main__":
    pythiasettings = PythiaParams()
    parser = argparse.ArgumentParser("submit_pythia.py", description="Submitter for PYTHIA showering")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory with POWHEG chunks")
    parser.add_argument("outputbase", metavar="OUTPUTBASE", type=str, help="Location for PYTHIA output")
    parser.add_argument("pythiaversion", metavar="PYTHIAVERSION", type=str, help="PYTHIA version")
    parser.add_argument("-n", "--nchunk", metavar="NCHUNK", type=int, default=5, help="Number of chunks")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="default", help="PYTHIA macro (from repository)")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="SLURM partition")
    parser.add_argument("-t", "--timelimit", metavar="TIMELIMIT", type=str, default="10:00:00", help="Max allowed time (in h:m::s)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    pythiasettings.define_args(parser)
    args = parser.parse_args()
    setup_logging(args.debug)
    pythiasettings.parse_args(args)
    pythiasettings.log()

    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)
    fast_partition = get_fast_partition(cluster)
    
    if not find_pythiaversion(args.pythiaversion):
        logging.error("PYTHIA version %s not supported", args.pythiaversion)
        sys.exit(1)
    logging.info("Submitting showering with PYTHIA version %s of POWHEG events under %s", args.pythiaversion, args.inputdir)
    outputdir = os.path.join(os.path.abspath(args.outputbase), args.pythiaversion)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)
    pythiajob = submit_pythia(cluster, outputdir, args.inputdir, args.nchunk, args.pythiaversion, args.macro, pythiasettings, partition, args.timelimit)
    logging.info("Submitted PYTHIA job under ID %d", pythiajob)
    mergejob = submit_merge(cluster, outputdir, "Pythia8JetSpectra.root", fast_partition, pythiajob)
    logging.info("Submitted merging job under ID %d", mergejob)
    #cleanjob = submit_clean(cluster, outputdir, fast_partition, pythiajob)
    #logging.info("Submitted cleaning job under ID %d", cleanjob)
