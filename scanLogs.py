#! /usr/bin/env python3

import argparse
import logging
import os

def scan_file(filename: str) -> tuple:
    good = True
    host = ""
    with open(filename, "r") as reader:
        for line in reader:
            if "slurmstepd" in line:
                good = False
            if "Running on host:" in line:
                hostname = line.replace("Running on host:", "")
                host = hostname.lstrip().rstrip()
        reader.close()
    return (good, host)

def scan_logdir(logdir: str):
    bad_hosts = []
    for logfile in os.listdir(logdir):
        fulllogfile = os.path.join(logdir, logfile)
        status, host = scan_file(fulllogfile)
        if not status:
            if not host in bad_hosts:
                bad_hosts.append(host)
    if len(bad_hosts):
        logging.warning("Found bad hosts:")
        logging.warning("============================")
        for host in sorted(bad_hosts):
            logging.warning(host)
    else:
        logging.info("No bad host found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--logdir", metavar="LOGDIR", type=str, required=True, help="Directory with logfiles")
    args = parser.parse_args()
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
    scan_logdir(args.logdir)