#! /usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
from helpers.setup_logging import setup_logging
from helpers.cluster import get_cluster, get_default_partition

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

def find_pwgevents(inputdir: str, eventfile: str = "pwgevents.lhe"):
	result = []
	for root, dirs, files in os.walk(inputdir):
		for fl in files:
			if eventfile in fl:
				result.append(os.path.join(os.path.abspath(root), fl))
	return sorted(result)

def build_logfile(logfile: str):
    logdir = os.path.dirname(logfile)
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    return logfile

def submit(command: str, cluster: str, jobname: str, logfile: str, partition: str, arraysize: int = 0, timelimit: str = "10:00:00", memory: str = "4G", dependency: int = -1) -> int:
    logging.info("Using logfile: %s", logfile)
    submitcmd = "sbatch "
    if cluster == "CADES":
        submitcmd += " -A birthright" 
    submitcmd += " -N 1 -n 1 -c 1"
    submitcmd += " --partition {}".format(partition)
    submitcmd += " -J {}".format(jobname)
    submitcmd += " -o {}".format(logfile)
    if cluster == "CADES":
        submitcmd += " --time={}".format(timelimit)
        submitcmd += " --mem={}".format(memory)
    if arraysize > 0:
        submitcmd += " --array=0-{}".format(arraysize-1)
    if dependency > -1:
        submitcmd += " -d {}".format(dependency)
    submitcmd += " {}".format(command)
    submitResult = subprocess.run(submitcmd, shell=True, stdout=subprocess.PIPE)
    sout = submitResult.stdout.decode("utf-8")
    toks = sout.split(" ")
    jobid = int(toks[len(toks)-1])
    return jobid

def submit_clean(cluster: str, outputbase: str, partition: str, dependency: int) -> int:
    script = os.path.join(repo, "pythia_clean.sh")
    command = "{} {}".format(script, outputbase)
    logfile = build_logfile(os.path.join(outputbase, "logs", "clean.log"))
    return submit(command, cluster, "clean_py", logfile, partition, 0, "00:10:00", "2G", dependency)

def submit_merge(cluster: str, outputbase: str, rootfile: str, partition: str, dependency: int):
    script = os.path.join(repo, "pythia_merge.sh")
    command = "{} {} {} {} {}".format(script, cluster, repo, outputbase, rootfile)
    logfile = build_logfile(os.path.join(outputbase, "logs", "merge.log"))
    return submit(command, cluster, "merge_py", logfile, partition, 0, "01:00:00", "4G", dependency) 

def submit_pythia(cluster: str, outputdir: str, inputdir: str, chunksize: int, pythiaver: str, variation: str, partition: str, timelimit: str = "10:00:00") -> int:
    vartype = "NONE"
    varvalue = "NONE"
    if ":" in variation:
        tokens = variation.split(":")
        vartype = tokens[0]
        varvalue = tokens[1]
    files = find_pwgevents(inputdir)
    logging.info("Found %d files", len(files))
    filelists = split(os.path.join(outputdir, "filelists"), files, chunksize)
    logging.info("Submitting %d PYTHIA jobs", len(filelists))
    command = ""
    if pythiaver == "original":
        # Hadi's original script, interfaced via rootpythia8
        script = os.path.join(repo, "pythia_steer_original.sh")
        command = "{} {} {} {} {} {}".format(script, cluster, repo, outputdir, vartype, varvalue)
    else:
        script = os.path.join(repo, "pythia_steer.sh")
        command = "{} {} {} {} {} {} {}".format(script, cluster, repo, outputdir, pythiaver, vartype, varvalue)
    logfile = build_logfile(os.path.join(outputdir, "logs", "pythia%a.log"))
    return submit(command, cluster, "py_{}".format(pythiaver), logfile, partition, len(filelists), timelimit)

def find_pythiaversion(pythiaversion: str) -> bool:
    if pythiaversion == "FromROOT" or pythiaversion == "FromALICE" or pythiaversion == "original" :
        return True
    simsoft = "/nfs/data/alice-dev/mfasel_alice/simsoft"
    modulelocation = os.path.join(simsoft, "Modules", "PYTHIA")
    for mod in os.listdir(modulelocation):
        if mod == pythiaversion:
            return True
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_pythia.py", description="Submitter for PYTHIA showering")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory with POWHEG chunks")
    parser.add_argument("outputbase", metavar="OUTPUTBASE", type=str, help="Location for PYTHIA output")
    parser.add_argument("pythiaversion", metavar="PYTHIAVERSION", type=str, help="PYTHIA version")
    parser.add_argument("-n", "--nchunk", metavar="NCHUNK", type=int, default=5, help="Number of chunks")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="SLURM partition")
    parser.add_argument("-t", "--timelimit", metavar="TIMELIMIT", type=str, default="10:00:00", help="Max allowed time (in h:m::s)")
    parser.add_argument("-v", "--variation", metavar="VARIATION", type=str, default="NONE", help="Systematic variation (TYPE:VALUE)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)
    
    if not find_pythiaversion(args.pythiaversion):
        logging.error("PYTHIA version %s not supported", args.pythiaversion)
        sys.exit(1)
    logging.info("Submitting showering with PYTHIA version %s of POWHEG events under %s", args.pythiaversion, args.inputdir)
    outputdir = os.path.join(os.path.abspath(args.outputbase), args.pythiaversion)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)
    pythiajob = submit_pythia(cluster, outputdir, args.inputdir, args.nchunk, args.pythiaversion, args.variation, partition, args.timelimit)
    logging.info("Submitted PYTHIA job under ID %d", pythiajob)
    mergejob = submit_merge(cluster, outputdir, "Pythia8JetSpectra.root", partition, pythiajob)
    logging.info("Submitted merging job under ID %d", mergejob)
    cleanjob = submit_clean(cluster, outputdir, partition, pythiajob)
    logging.info("Submitted cleaning job under ID %d", cleanjob)