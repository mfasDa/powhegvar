#! /usr/bin/env python3

import os
import sys

if __name__ == "__main__":
    inputfile = sys.argv[1]
    workdir = os.path.dirname(inputfile)
    outputfile = os.path.join(workdir, "checksummary_pwgevents_patched.log")
    with open(outputfile, 'w') as outputwriter:
        with open(inputfile, 'r') as inputreader:
            for line in inputreader:
                outputwriter.write("{}\n".format(line.replace("\n", "")))
            inputreader.close()
        missing = []
        for i in range(0, int(sys.argv[2])):
            
            testfile = os.path.join(workdir, "%04d" %i, "pwgevents.lhe")
            if not os.path.exists(testfile):
                missing.append(testfile)
        if len(missing):
            outputwriter.write("[INFO]: Incomplete pwgevents.lhe files:\n")
            for missfile in sorted(missing):
                outputwriter.write(f"[INFO]: {missfile}\n")
            outputwriter.write("[INFO]: ----------------------------------------\n")
        outputwriter.close()