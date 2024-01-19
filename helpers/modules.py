#! /usr/bin/env python3
import os

def find_powheg_releases() -> list:
    simpath = "/nfs/data/alice-dev/mfasel_alice/simsoft/"
    files = [x for x in os.listdir(os.path.join(simpath, "Modules", "POWHEG"))]
    # Allow to run as well with POWHEG from alidist
    files.append("FromALICE")
    return files

def find_pythiaversion(pythiaversion: str) -> bool:
    if pythiaversion == "FromROOT" or pythiaversion == "FromALICE" or pythiaversion == "original" :
        return True
    simsoft = "/nfs/data/alice-dev/mfasel_alice/simsoft"
    modulelocation = os.path.join(simsoft, "Modules", "PYTHIA")
    for mod in os.listdir(modulelocation):
        if mod == pythiaversion:
            return True
    return False

def get_OSVersion(cluster: str, powheg_version: str):
    if not cluster == "CADES":
        return ""
    return "CentOS7" if powheg_version.startswith("r") else "CentOS8"

def get_pythia_OSVersion(cluster: str, pythia_version: str):
    if not cluster == "CADES":
        return ""
    return "CentOS8" if pythia_version == "FromALICE" or pythia_version == "FromROOT" else "CentOS7"
