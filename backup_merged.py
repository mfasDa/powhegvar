#! /usr/bin/env python3
import argparse
import logging
import os
import shutil
from helpers.setup_logging import setup_logging

def find_files(inputdir: str, rootfile: str):
    outfiles = []
    for root,dirs,files in os.walk(inputdir):
        for fl in files:
            if rootfile in fl:
                outfiles.append(os.path.abspath(os.path.join(root, fl)))
    return outfiles

def copy_to_output(outputdir: str, inputfile: str, inputdir: str):
    outputfile = inputfile
    outputfile = outputfile.replace(inputdir, outputdir)
    fileoutputdir = os.path.dirname(outputfile)
    if not os.path.exists(fileoutputdir):
        os.makedirs(fileoutputdir, 0o755)
    logging.info("Copying %s to %s", inputfile, outputfile)
    shutil.copyfile(inputfile, outputfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("backup_merged.py", description="Copy to final location")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input directory")
    parser.add_argument("outputdir", metavar="OUTPUTDIR", type=str, help="Output directory")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default="Pythia8JetSpectra_merged.root", help="ROOT file to be copied")
    args = parser.parse_args()
    setup_logging()

    inputdir = os.path.abspath(args.inputdir)
    outputdir = os.path.abspath(args.outputdir) 
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)
    for fl in find_files(inputdir, args.file):
        copy_to_output(outputdir, fl, inputdir)