#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging
from helpers.slurm import submit
from helpers.modules import find_powheg_releases

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def submit_job(cluster: str, workdir: str, powheg_version: str, powheg_input: str, minpdf: int, maxpdf: int, minid: int, partition: str, njobs: int, mem: int = 4, hours: int = 10, dependency: int = 0):
    print("Submitting POWHEG release {}".format(powheg_version))
    logdir = os.path.join(workdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_{}_{}_%a.log".format(minpdf, maxpdf))
    executable = os.path.join(repo, "powheg_steer_pdf.sh")
    runcmd = "{} {} {} {} {} {} {} {} {}".format(executable, cluster, repo, workdir, powheg_version, powheg_input, minpdf, maxpdf, minid)
    jobname = "pdfvar".format(powheg_version)
    return submit(runcmd, cluster, jobname, logfile, get_default_partition(cluster) if partition == "default" else partition, njobs, "{}:00:00".format(hours), "{}G".format(mem), dependency=dependency)

def find_number_of_input_files(workdir: str):
    pwgdirs = [x for x in os.listdir(workdir) if os.path.isfile(os.path.join(workdir, x, "pwgevents.lhe"))]
    return len(pwgdirs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_powheg.py", description="Submitter for powheg")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("minpdf", metavar="MINPDF", type=int, help="Min. PDF set number")
    parser.add_argument("maxpdf", metavar="MAXPDF", type=int, help="Max. PDF")
    parser.add_argument("minid", metavar="MINID", type=int, default=1, help="Min. weight ID")
    parser.add_argument("-i", "--input", metavar="POWHEGINPUT", type=str, default=os.path.join(repo, "powheginputs", "powheg_13TeV_CT14_default.input"), help="POWHEG input")
    parser.add_argument("-v", "--version", metavar="VERSION", type=str, default="r3898", help="POWEHG version")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("--dependency", metavar="DEPENDENCY", type=int, default=-1, help="Dependency")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
  
    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)

    if not os.path.exists(args.workdir):
        logging.error("Working directory %s doesn't exist", args.workdir)
        sys.exit(1)
    njobs = find_number_of_input_files(args.workdir)
    if njobs == 0:
        logging.error("Didn't find slot dirs with pwgevents.lhe in %s", args.workdir)
        sys.exit(1)
    releases_all = find_powheg_releases() if cluster == "CADES" else ["default"]
    request_release = args.version if cluster == "CADES" else "default"
    if not request_release in releases_all:
        print("requested POWHEG not found: {}".format(args.version))
        sys.exit(1)
    print("Simulating with POWHEG: {}".format(args.version))
    pwhgjob = submit_job(cluster, args.workdir, args.version, args.input, args.minpdf, args.maxpdf, args.minid, args.partition, njobs, args.mem, args.hours, args.dependency)
    logging.info("Job ID: %d", pwhgjob)
	
