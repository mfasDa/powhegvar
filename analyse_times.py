#! /usr/bin/env python3

import argparse
import logging
import os
import statistics

from matplotlib import pyplot as plt
from numpy import array

from helpers.setup_logging import setup_logging

def histogram_times(jobtimes: list, outputfile: str, tag: str = ""):
    data = array(jobtimes)
    values, bins, patches = plt.hist(data, 50, density=True, facecolor='g', alpha=0.75)

    meantime = statistics.mean(jobtimes)
    stddevtime = statistics.stdev(jobtimes)
    maxtime = max(jobtimes)
    mintime = min(jobtimes)
    logging.info("Extracted  time: %f +- %f sec [%d - %d sec]", meantime, stddevtime, mintime, maxtime)

    maxval = max(values)
    axismin = bins[0]
    axismax = bins[50]
    
    plottitle = "Job time"
    if len(tag):
        plottitle += f" ({tag})"

    plt.xlabel('Job time (sec)')
    plt.ylabel('Probability')
    plt.title(plottitle)
    plt.text(meantime - 2*stddevtime, .85 * maxval, r'$\mu=%d sec,\ \sigma=%d sec$' %(meantime, stddevtime))
    plt.axis([axismin, axismax, 0, 1.1*maxval])
    plt.grid(True)
    for filetype in ["pdf", "png"]:
        plt.savefig(f"{outputfile}.{filetype}")

def get_jobtime_seconds(logfile: str) -> int:
    logging.info("Reading %s", logfile)
    seconds = 0
    with open(logfile, "r") as logreader:
        for line in logreader:
            if "POWHEG processing finished" in line:
                index_total = line.index("(")+1
                index_total_end = line.index(")")
                total = line[index_total:index_total_end]
                seconds = int(total.split(" ")[0])
                break
    return seconds

def find_logs(workdir: str, pattern: str) -> list:
    files = []
    for fl in os.listdir(os.path.join(workdir, "logs")):
        if not fl.endswith("log"):
            continue
        testfile = fl
        index = testfile.replace(".log", "").replace(pattern, "")
        if not index.isdigit():
            continue
        files.append(fl)
    return sorted(files)

def filter_times(jobtimes: list) -> list:
    return [x for x in jobtimes if x > 0]

def get_jobtimes(workdir: str, pattern: str) -> list:
    return [get_jobtime_seconds(os.path.join(workdir,"logs",x)) for x in find_logs(workdir, pattern)]

def process(workdir: str, pattern: str, outputfile: str, tag: str):
    histogram_times(filter_times(get_jobtimes(workdir, pattern)), outputfile, tag)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("analyse_times.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("pattern", metavar="PATTERN", type=str, help="Pattern of log files")
    parser.add_argument("outputfile", metavar="OUTPUTFILE", type=str, help="Output file")
    parser.add_argument("-t", "--tag", metavar="TAG", type=str, default="", help="Tag (in histogram title)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging(args.debug)
    process(args.workdir, args.pattern, args.outputfile, args.tag)