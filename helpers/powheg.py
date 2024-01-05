#! /usr/bin/env python3
import logging
import os
import random


def get_valid_processes() -> list:
    return ["dijet", "directphoton", "hvq", "W", "Z"]

def is_valid_process(procname: str) -> bool:
    return procname in get_valid_processes()

def load_pwginput(inputfile: str) -> dict:
    lines = {}
    with open(inputfile, "r") as reader:
        for line in reader:
            line = line.rstrip("\n")
            if not len(line):
                continue
            line = line.lstrip()
            if line.startswith("!") or line.startswith("#"):
                #line commented out
                continue
            commenttoken = -1
            if "!" in line or "#" in line:
                if "!" in line:
                    commenttoken = line.find("!")
                elif "#" in line:
                    commenttoken = line.find("#")
            command = line
            if commenttoken >= 0:
                command = line[:commenttoken]
            if not len(command):
                continue
            tokens = command.split(" ")
            key = ""
            value = "" 
            for tok in tokens:
                if not len(tok):
                    continue
                if not len(key):
                    key = tok.lstrip().rstrip()
                elif not len(value):
                    value = tok.lstrip().rstrip()
            lines[key] = value
        reader.close()
    return lines

def check_compatible(targetfile: str, inputfile: str, ignore_keys: str) -> bool:
    config_target = load_pwginput(targetfile)
    config_input = load_pwginput(inputfile)
    match_target = True
    match_input = True
    def has_ignorekey(line: str, keys: list) -> bool:
        found = False
        for key in keys:
            if key in line:
                found = True
                break
        return found
    for key,value in config_input.items():
        if has_ignorekey(key, ignore_keys):
            continue
        if not key in config_target.keys():
            match_target = False
            break
        elif not value == config_target[key]:
            match_target = False
            break
    for key,value in config_target.items():
        if has_ignorekey(key, ignore_keys):
            continue
        if not key in config_input.keys():
            match_input = False
            break
        elif not value == config_input[key]:
            match_input = False
            break
    if match_input and match_target:
        return True
    return False

def build_powheg_stage(inputfile: str, workdir: str, stage: int, xgrid_iter: int, nslot: int, nevents: int, outputfile: str = "default"):
    if outputfile == "default":
        outputfile = os.path.join(workdir, "powheg.input")
    if os.path.exists(outputfile):
        ignorekeys = ["numevts", "manyseeds", "maxseeds", "parallelstage", "xgriditeration", "storemintupb"]
        if not check_compatible(outputfile, inputfile, ignorekeys):
            logging.error("Configurations %s and %s not compatible", inputfile, outputfile)
        os.remove(outputfile)
    has_stage = False
    has_nevents = False
    has_xgriditer = False
    has_manyseeds = False
    has_maxseeds = False
    has_storemintupb = False
    with open(outputfile, "w") as writer:
        with open(inputfile, "r") as reader:
            for line in reader:
                if "numevts" in line:
                    if stage == 4:
                        writer.write("numevts {}\n".format(nevents))
                    else:
                        writer.write("{}\n".format(line.rstrip("\n")))
                    has_nevents = True
                elif "manyseeds" in line:
                    writer.write("manyseeds 1\n")
                    has_manyseeds = True
                elif "maxseeds" in line:
                    writer.write("maxseeds {}\n".format(nslot))
                    has_maxseeds = True
                elif "parallelstage" in line:
                    writer.write("parallelstage {}\n".format(stage))
                    has_stage = True
                elif "xgriditeration" in line:
                    if stage == 1:
                        writer.write("xgriditeration {}\n".format(xgrid_iter))
                    has_xgriditer = True
                elif "storemintupb" in line:
                    if stage == 1 or stage == 2:
                        writer.write("storemintupb 1\n")
                    has_storemintupb = True
                else:
                    writer.write("{}\n".format(line.rstrip("\n")))
            reader.close()
        if not has_manyseeds:
            writer.write("manyseeds 1\n")
        if not has_maxseeds:
            writer.write("maxseeds {}\n".format(nslot))
        if not has_stage:
            writer.write("parallelstage {}\n".format(stage))
        if stage == 1:
            if not has_xgriditer:
                writer.write("xgriditeration {}\n".format(xgrid_iter))
            if not has_storemintupb:
                writer.write("storemintupb 1\n")
        if stage == 4:
            if not has_nevents:
                writer.write("numevts {}\n".format(nevents))
        writer.close()

def build_powhegseeds(workdir: str, nseeds: int = 1000000, seedfile: str = "default"):
    if seedfile == "default":
        seedfile = os.path.join(workdir, "pwgseeds.dat")
    if os.path.exists(seedfile):
        os.remove(seedfile)
    with open(seedfile, "w") as writer:
        for iseed in range(0, max(nseeds, 20)): 
            rnd = random.randint(0, 1073741824)  # 2^30
            writer.write("{}\n".format(rnd))
        writer.close()
