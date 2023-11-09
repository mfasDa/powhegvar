#! /usr/bin/env python3
import logging
import os

def replace_value(input: str, newvalue: str):
    command = input
    if "!" in command:
        command = command[:command.find("!")-1]
    if "#" in command:
        command = command[:command.find("#")-1]
    tokens = command.split(" ")
    stripped_tokens = []
    for tok in tokens:
        if len(tok):
            stripped_tokens.append(tok)
    oldvalue = stripped_tokens[1]
    logging.debug("Replaceing %s with %s", oldvalue, newvalue)
    output = input.replace(oldvalue, newvalue)
    logging.debug("New line: %s", output)
    return output


def get_energy_from_config(configfile: str) -> float:
    energy = 0.
    if os.path.exists(configfile):
        with open(configfile, "r") as configreader:
            ebeam1 = 0
            ebeam2 = 0
            for command in configreader:
                if not "ebeam" in command:
                    continue
                if "!" in command:
                    command = command[:command.find("!")-1]
                if "#" in command:
                    command = command[:command.find("#")-1]
                tokens = command.split(" ")
                stripped_tokens = [] 
                for tok in tokens:
                    if len(tok):
                        stripped_tokens.append(tok)
                beamenergy = tokens[1]
                if "d" in beamenergy:
                    beamenergy = beamenergy.replace("d", ".")
                beamenergy_float = float(beamenergy)
                if tokens[0] == "ebeam1":
                    ebeam1 = beamenergy_float
                elif tokens[0] == "ebeam2":
                    ebeam2 = beamenergy_float
            energy = ebeam1 + ebeam2
    return energy
