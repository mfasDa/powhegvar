#! /usr/bin/env python3
import argparse
import logging
import os

class weight_entry:

    def __init__(self, id: str ="", description: str = ""):
        self.__id = id
        self.__description = description

    def __lt__(self, other):
        if isinstance(other, weight_entry):
            return self.__id < other.__id
        return False
    
    def __eq__(self, other):
        if isinstance(other, weight_entry):
            return self.__id == other.__id
        return False

    def set_id(self, id: str):
        self.__id = id

    def set_description(self, description: str):
        self.__description = description

    def get_id(self) -> str:
        return self.__id
    
    def get_description(self) -> str:
        return self.__description

    id = property(fget=get_id, fset=set_id)
    description = property(fget=get_description, fset=set_description)

class weight_group:

    def __init__(self, name: str):
        self.__name = name
        self.__weights = []

    def __lt__(self, other):
        if isinstance(other, weight_group):
            return self.__name < other.__name
        return False
    
    def __eq__(self, other):
        if isinstance(other, weight_entry):
            return self.__name == other.__name
        return False

    def set_name(self, name: str):
        self.__name == name

    def add_weight(self, weight: weight_entry):
        self.__weights.append(weight)

    def add_weight(self, id: str, description: str):
        self.__weights.append(weight_entry(id, description))
    
    def add_weights(self, weights: list):
        for entry in weights:
            self.add_weight(entry)

    def get_name(self) -> str:
        return self.__name

    def get_list_of_weights(self) -> list:
        return self.__weights

    def has_weight(self, id: str) -> bool:
        return self.find_weight(id) != None

    def find_weight(self, id: str) -> weight_entry:
        found = [x for x in self.__weights if x.id  == id ]
        if not len(found) or len(found) > 1:
            return None
        return found[0]

    name = property(fget=get_name, fset=set_name)

class pwgevents_info:

    def __init__(self):
        self.__nevents = 0
        self.__weights = []
        self.__weightgroups = []
        self.__closingmarker = False
        self.__exists = False
        self.__nonempty = False

    def set_nevents(self, nevents: str):
        self.__nevents = nevents

    def set_closingmarker(self, doSet: bool):
        self.__closingmarker = doSet

    def set_fileexists(self, doSet: bool):
        self.__exists = doSet

    def set_nonempty(self, doSet: bool):
        self.__nonempty = doSet

    def add_event(self):
        self.__nevents += 1

    def get_nevents(self) -> int:
        return self.__nevents

    def has_closingmarker(self) -> bool:
        return self.__closingmarker

    def is_file_existing(self) -> bool:
        return self.__exists
    
    def is_file_nonempty(self) -> bool:
        return self.__nonempty

    def add_weight_non_grouped(self, id: str, description: str):
        if not self.find_weight(id):
            self.__weights.append(weight_entry(id, description))

    def add_weight_in_group(self, weightgroup: str, id: str, description: str):
        foundgroup = self.find_weightgroup(weightgroup)
        if foundgroup != None:
            foundgroup.add_weight(id, description)
        else:
            nextgroup = weight_group(weightgroup)
            nextgroup.add_weight(id, description)
            self.__weightgroups.append(nextgroup)

    def get_weightgroups(self) -> list:
        return self.__weightgroups

    def get_weights_non_grouped(self) -> list:
        return self.__weights

    def get_all_weights(self) -> list:
        result = []
        for weight in self.__weights:
            result.append(weight)
        for grp in self.__weightgroups:
            for weight in grp.get_list_of_weights():
                result.append(weight)
        return sorted(result)

    def has_weightgroup(self, name) -> bool:
        return self.find_weightgroup(name) != None

    def has_weight(self, id: str) -> bool:
        return self.find_weight(id) != None
    
    def has_weight_non_grouped(self, id: str):
        return self.find_weight_non_grouped(id) == None

    def find_weightgroup(self, name) -> weight_group:
        found = [x for x in self.__weightgroups if x.name == name]
        if not len(found) or len(found) > 1:
            return None
        return found[0]
    
    def find_weight_non_grouped(self, id: str) -> weight_entry:
        found = [x for x in self.__weights if x.name == id]
        if not len(found) or len(found) > 1:
            return None
        return found[0]

    def find_weight(self, id: str) -> weight_entry:
        result = None
        found = [x for x in self.__weights if x.id == id]
        if len(found) == 1:
            # weight is non-grouped
            result = found[0]
        else:
            # check whether weight is grouped
            groupresult = None
            for grp in self.__weightgroups:
                groupresult = grp.find_weight(id)
                if groupresult:
                    result = groupresult
                    break
        return result


    nevents = property(fget=get_nevents, fset=set_nevents)
    closingmarker = property(fget=has_closingmarker, fset=set_closingmarker)
        
class HeaderParser:

    def __init__(self):
        self.__lines = []

    def add_line(self, line: str):
        self.__lines.append(line)

    def decode(self, pwgsummary: pwgevents_info):
        logging.debug("Start decoding header")
        currentweightgroup = None
        for line in self.__lines:
            if line.startswith("<weightgroup"):
                logging.debug("New weight group found")
                groupname, combine = self.decode_weightgroup(line)
                logging.debug("Decoded group name: %s", groupname)
                currentweightgroup = groupname
            if line.startswith("</weightgroup>"):
                logging.debug("Weight group complete")
                currentweightgroup = None
            if line.startswith("<weight id"):
                logging.debug("New weight found")
                id, description = self.decode_weight(line)
                logging.debug("Decoded ID: %s, description: %s", id, description)
                if currentweightgroup:
                    pwgsummary.add_weight_in_group(currentweightgroup, id, description)
                else:
                    pwgsummary.add_weight_non_grouped(id, description)

    def decode_weightgroup(self, weightgroupinfo: str) -> tuple:
        tokens = weightgroupinfo.lstrip("<").rstrip(">").split(" ")
        name = ""
        combine = ""
        for tok in tokens:
            if not "=" in tok:
                continue
            keyval = tok.split("=")
            key = keyval[0]
            value = keyval[1].lstrip("\'").rstrip("\'")
            if key == "name":
                name= value
            elif key == "combine":
                combine = value
        return (name, combine)

    def decode_weight(self, weightinfo: str):
        id = ""
        description = ""
        delim_open = weightinfo.find(">")
        tag = weightinfo[0:delim_open+1]
        next = weightinfo[delim_open+1:]
        taginfos = tag.lstrip("<").rstrip(">").split(" ")
        for info in taginfos:
            if not "=" in info:
                continue
            keyval = info.split("=")
            key = keyval[0]
            value = keyval[1].lstrip("\'").rstrip("\'")
            if key == "id":
                id = value
        delim_end = next.find("</weight>")
        description=next[:delim_end].lstrip().rstrip()
        return (id, description)


def parse_file(pwgevents: str) ->pwgevents_info:
    result = pwgevents_info()
    headerdecoder = HeaderParser()
    header_open = False
    event_open = False 
    if os.path.exists(pwgevents):
        result.set_fileexists(True)
    nlines = 0
    with open(pwgevents, "r") as pwgreader:
        for line in pwgreader:
            nlines += 1
            line_trunc = line.lstrip().rstrip()
            if line_trunc.startswith("<header>"):
                logging.debug("Start header marker found")
                header_open = True
            elif line_trunc.startswith("</header>"):
                logging.debug("Closing header maker found")
                if header_open:
                    logging.debug("Start decoding header")
                    headerdecoder.decode(result)
                header_open = False
            elif line_trunc.startswith("<event>"):
                event_open = True
            elif line_trunc.startswith("</event>"):
                if event_open:
                    result.add_event()
                event_open = False
            elif line_trunc.startswith("</LesHouchesEvents>"):
                result.set_closingmarker(True)
            else:
                if header_open:
                    headerdecoder.add_line(line_trunc)
    if nlines > 0:
        result.set_nonempty(True)
    return result

def analyse_pwgevents(pwgevents: str, summaryfile: str):
    decoded = parse_file(pwgevents)
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