#! /usr/bin/env python3

import argparse
import logging
import os
from helpers import setup_logging

class checkinfo:

    def __init__(self, filename):
        self.__filename = filename
        self.__exits = False
        self.__nonempty = False
        self.__complete = False
        self.__events = 0
        self.__weights = []

    def set_filename(self, filename: str):
        self.__filename = filename

    def set_exist(self, doSet: bool):
        self.__exits = doSet

    def set_nonempty(self, doSet: bool):
        self.__nonempty = doSet

    def set_complete(self, doSet: bool):
        self.__complete = doSet

    def set_events(self, events: int):
        self.__events = events

    def get_filename(self) -> str:
        return self.__filename

    def is_existing(self) -> bool:
        return self.__exits
    
    def is_nonempty(self) -> bool:
        return self.__nonempty

    def is_complete(self) -> bool:
        return self.__complete

    def get_events(self) -> int:
        return self.__events

    def add_weight(self, weight: str):
        self.__weights.append(weight)

    def get_list_of_weights(self) -> list:
        return self.__weights

    def has_weight(self, weight: str):
        return weight in self.__weights

    def has_all_weights(self, weighttypes: list) -> bool:
        foundMissing = False
        for weighttype in weighttypes:
            if not weighttype in self.__weights:
                foundMissing = True
                break
        if foundMissing:
            return False
        return True

    def get_missing_weights(self, expectweights: list) -> list:
        missing = []
        for weight in expectweights:
            if not weight in self.__weights:
                missing.append(weight)
        return sorted(missing)

    filename = property(fget=get_filename, fset=set_filename)
    exists = property(fget=is_existing, fset=set_exist)
    nonempty = property(fget=is_nonempty, fset=set_nonempty)
    complete = property(fget=is_complete, fset=set_complete)
    events = property(fget=get_events, fset=set_events)


def parse_checkfile(checkfile: str) -> checkinfo:
    result = checkinfo(checkfile)
    with open(checkfile, "r") as checkreader:
        for line in checkreader:
            line_strip = line.rstrip("\n")
            keyval = line_strip.split(":")
            key = keyval[0].lstrip().rstrip()
            value = keyval[1].lstrip().rstrip()
            if key == "exists":
                result.exists = True if value == "yes" else False
            elif key == "nonempty":
                result.nonempty = True if value == "yes" else False
            elif key == "complete":
                result.complete = True if value == "yes" else False
            elif key == "events":
                result.events = int(value)
            elif key == "weights":
                weights = value.split(",")
                for weight in weights:
                    weight_stripped = weight.lstrip().rstrip()
                    if not len(weight_stripped):
                        continue
                    result.add_weight(weight_stripped)
    return result

def find_checkfiles(workdir: str) -> list:
    result = []
    for root,dirs,files in os.walk(os.path.abspath(workdir)):
        for fl in files:
            if "check_pwgevents.txt" in fl:
                result.append(os.path.join(root, fl))
    return sorted(result)

def build_checkinfos(workdir: str) -> list:
    return [parse_checkfile(x) for x in find_checkfiles(workdir)]

def get_total_events(infos: list) -> int:
    sumEvents = 0
    for info in infos:
        sumEvents += info.events
    return sumEvents

def get_weighttypes(infos: list) -> list:
    weighttypes = []
    for info in infos:
        for weight in info.get_list_of_weights():
            if not weight in weighttypes:
                weighttypes.append(weight)
    return weighttypes

def get_number_checkinfos(infos: list) -> int:
    return len(infos)

def get_number_existing(infos: list) -> int:
    return len([x for x in infos if x.exists])

def filter_nonexisting(infos: list) -> list:
    return [x for x in infos if not x.exists]

def get_number_nonempty(infos: list) -> int:
    return len([x for x in infos if x.nonempty])

def filter_empty(infos: list) -> list:
    return [x for x in infos if x.exists and not x.nonempty]

def get_number_complete(infos: list) -> int:
    return len([x for x in infos if x.complete])

def filter_incomplete(infos: list) -> list:
    return [x for x in infos if x.exists and x.nonempty and not x.complete]

def get_number_allweights(infos: list, weighttypes: list) -> int:
    return len([x for x in infos if x.nonempty and x.has_all_weights(weighttypes)])

def filter_not_allweights(infos: list, weighttypes: list) -> list:
    return [x for x in infos if x.nonempty and not x.has_all_weights(weighttypes)]

def get_weightypestring(weighttypes: list) -> str:
    result = ""
    first = True
    for weighttype in weighttypes:
        if first:
            first = False
        else:
            result += ", "
        result += weighttype
    return result

def make_eventfile(checkfile: str):
    return checkfile.replace("check_pwgevents.txt", "pwgevents.lhe")

def analyse(workdir: str):
    infos = build_checkinfos(workdir)
    logging.info("Number of checkinfos:               %d", get_number_checkinfos(infos))
    logging.info("Number of existing files:           %d", get_number_existing(infos))
    logging.info("Number of nonempty files:           %d", get_number_nonempty(infos))
    logging.info("Number of complete files:           %d", get_number_complete(infos))
    allweights = get_weighttypes(infos)
    logging.info("Number of files with all weights:   %d", get_number_allweights(infos, allweights))
    logging.info("Number of events:                   %d", get_total_events(infos))
    logging.info("Found weight IDs:                   %s", get_weightypestring(allweights))
    files_nonexisting = filter_nonexisting(infos)
    files_empty = filter_empty(infos)
    files_incomplete = filter_incomplete(infos)
    files_notallweights = filter_not_allweights(infos, allweights)
    if len(files_nonexisting):
        logging.info("Non-existing pwgevents.lhe files:")
        for fl in files_nonexisting:
            logging.info(make_eventfile(fl.filename))
        logging.info("----------------------------------------")
    if len(files_empty):
        logging.info("Empty pwgevents.lhe files:")
        for fl in files_empty:
            logging.info(make_eventfile(fl.filename))
        logging.info("----------------------------------------")
    if len(files_incomplete):
        logging.info("Incomplete pwgevents.lhe files:")
        for fl in files_incomplete:
            logging.info(make_eventfile(fl.filename))
        logging.info("----------------------------------------")
    if len(files_notallweights):
        logging.info("pwgevents.lhe files with missing weights:")
        for fl in files_notallweights:
            logging.info("%s (missing: %s)", make_eventfile(fl.filename), get_weightypestring(fl.get_missing_weights(allweights)))
        logging.info("----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("scan_check_pwgevents.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    setup_logging.setup_logging(args.debug)
    analyse(args.workdir)