#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.setup_logging import setup_logging
from helpers.slurm import submit_range

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(workdir: str, powheg_version: str, njobs: int, minslot: int = 0, mem: int = 4, hours: int = 10):
	print("Submitting POWHEG release {}".format(powheg_version))
	logdir = os.path.join(workdir, "POWHEG_{}".format(powheg_version), "logs")
	if not os.path.exists(logdir):
		os.makedirs(logdir, 0o755)
	logfile = os.path.join(logdir, "joboutput%a.log")
	executable = os.path.join(repo, "powheg_steer.sh")
	runcmd = "{} {} {} {}".format(executable, repo, workdir, powheg_version)
	jobname = "pjj13T_{}".format(powheg_version)
	return submit_range(runcmd, jobname, logfile, "high_mem_cd", {"first": minslot, "last": minslot+njobs-1}, "{}:00:00".format(hours), "{}G".format(mem))
	#batchsettings = "-A birthright -p high_mem_cd -N 1 -n 1 -c 1"
	#resources = "--mem={MEM}G -t {HRS}:00:00".format(MEM=mem, HRS=hours)
	#jobarray = "--array={}-{}".format(minslot, minslot+njobs-1)
	#submitcmd = "sbatch {SET} {RES} {ARR} -J {NAME} -o {LOG} {RUN}".format(SET=batchsettings, RES=resources, ARR=jobarray, NAME=jobname, LOG=logfile, RUN=runcmd)
	#subprocess.call(submitcmd, shell=True)

def find_powheg_releases() -> list:
	simpath = "/nfs/data/alice-dev/mfasel_alice/simsoft/"
	files = [x for x in os.listdir(os.path.join(simpath, "Modules", "POWHEG"))]
	return files

def prepare_outputlocation(outputlocation: str):
	if not os.path.exists(outputlocation):
		os.makedirs(outputlocation, 0o755)

if __name__ == "__main__":
	parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
	parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
	parser.add_argument("-n", "--njobs", metavar="NJOBS", type=int, default=200, help="Number of slots")
	parser.add_argument("-m", "--minslot", metavar="MINSLOT", type=int, default=0, help="Min. slot ID")
	parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="all", help="POWEHG version")
	parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
	parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
	parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
	args = parser.parse_args()
	setup_logging(args.debug)

	prepare_outputlocation(args.workdir)	
	releases = []
	release_all = find_powheg_releases()
	if args.version == "all":
		releases = release_all
	else:
		if not args.version:
			print("requested POWHEG not found: {}".format(args.version))
			sys.exit(1)
		releases.append(args.version)
		print("Simulating with POWHEG: {}".format(releases))
	for pwhg in releases:
		pwhgjob = submit_job(args.workdir, pwhg, args.njobs, args.minslot, args.mem, args.hours)
		logging.info("Job ID for POWHEG %s: %d", pwhg, pwhgjob)
	
