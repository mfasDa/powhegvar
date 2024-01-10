#! /usr/bin/env python3
import argparse
import logging
import os

from helpers.pwgeventsparser import pwgeventsparser

def analyse_pwgevents(pwgevents: str, summaryfile: str):
    parser = pwgeventsparser(pwgevents)
    parser.parse()
    decoded = parser.get_eventinfos()

    basedir = os.path.dirname(os.path.abspath(pwgevents))
    summaryfilename = os.path.join(basedir, summaryfile)
    with open(summaryfilename, "w") as summarywriter:
        summarywriter.write("exists: {}\n".format("yes" if decoded.is_file_existing() else "no"))
        summarywriter.write("nonempty: {}\n".format("yes" if decoded.is_file_nonempty() else "no"))
        summarywriter.write("events: {}\n".format(decoded.get_nevents()))
        summarywriter.write("complete: {}\n".format("yes" if decoded.closingmarker else "no"))
        weightids = decoded.get_all_weights()
        weightstring = "weights:"
        first = True
        for weight in weightids:
            if not first:
                weightstring += ","
            else:
                first = False
            weightstring += " {}".format(weight.id)
        summarywriter.write("{}\n".format(weightstring))
        summarywriter.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("checkPwgevents")
    parser.add_argument("-i", "--inputfile", metavar="INPUTFILE", required=True, type=str, help="pwgevents.lhe file to be checked")
    parser.add_argument("-o", "--outputfile", metavar="OUTPUTFILE", type=str, default="check_pwgevents.txt", help="File with summary information")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=loglevel)
    
    analyse_pwgevents(args.inputfile, args.outputfile)