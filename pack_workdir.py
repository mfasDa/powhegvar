#! /usr/bin/env python3

import argparse
import os
from zipfile import ZipFile


def process_directory(workdir: str):
    print("Processing %s" %workdir)
    os.chdir(workdir)
    logfiles = []
    pwginputs = []
    monfiles = []
    for fl in os.listdir(workdir):
        if fl.endswith(".log"):
            logfiles.append(fl)
        if fl.endswith(".input"):
            pwginputs.append(fl)
        if fl.endswith(".dat") or fl.endswith(".top") or fl.endswith(".txt"):
            monfiles.append(fl)
        if fl == "bornequiv" or fl == "FlavRegList" or fl == "pwhg_checklimits" or fl == "virtequiv":
            monfiles.append(fl)
        if fl.startswith("realequivregions"):
            monfiles.append(fl)
    logarchive = ZipFile("log_archive.zip", mode="w")
    for fl in logfiles:
        logarchive.write(fl)
    logarchive.close()
    inputarchive = ZipFile("input_archive.zip", mode="w")
    for fl in pwginputs:
        inputarchive.write(fl)
    inputarchive.close()
    monarchive = ZipFile("mon_archive.zip", mode="w")
    for fl in monfiles:
        monarchive.write(fl)
    monarchive.close()
    for fl in logfiles:
        os.remove(fl)
    for fl in pwginputs:
        os.remove(fl)
    for fl in monfiles:
        os.remove(fl)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("pack_workdir.py")
    parser.add_argument("-w", "--workdir", metavar="WORKDIR", type=str, default="", help="Working directory")
    parser.add_argument("-b", "--basedir", metavar="BASEDIR", type=str, default="", help="Base directory")
    args = parser.parse_args()
    if len(args.workdir):
        process_directory(os.path.abspath(args.workdir))
    elif len(args.basedir):
        for dr in os.listdir(args.basedir):
            if dr.isdigit():
                process_directory(os.path.join(os.path.abspath(args.basedir), dr))