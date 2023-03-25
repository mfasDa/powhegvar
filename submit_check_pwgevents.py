#! /usr/bin/env python3

import os
import argparse
import logging
import sys
from helpers.checkjob import submit_checks
from helpers.cluster import get_cluster, get_default_partition
from helpers.setup_logging import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_check_pwgevents.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-p", "--partition", metavar="PARTITION", type=str, default="default", help="Partition")
    parser.add_argument("-s", "--single", action="store_true", help="Submit single check job")
    parser.add_argument("--mem", metavar="MEMORY", type=int, default=4, help="Memory request in GB (default: 4 GB)" )
    parser.add_argument("--hours", metavar="HOURS", type=int, default=10, help="Max. numbers of hours for slot (default: 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)

    cluster = get_cluster()
    logging.info("Submitting for cluster %s", cluster)
    partition = args.partition if args.partition != "default" else get_default_partition(cluster)
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))

    if not os.path.exists(args.workdir):
        logging.error("Working directory %s doesn't exist", args.workdir)
        sys.exit(1)    
    submit_checks(cluster, repo, args.workdir, partition, -1, False if args.single else True)
