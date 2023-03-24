#! /usr/bin/env python3
import os

def find_powheg_releases() -> list:
    simpath = "/nfs/data/alice-dev/mfasel_alice/simsoft/"
    files = [x for x in os.listdir(os.path.join(simpath, "Modules", "POWHEG"))]
    # Allow to run as well with POWHEG from alidist
    files.append("FromALICE")
    return files

def get_OSVersion(cluster: str, powheg_version: str):
    if not cluster == "CADES":
        return ""
    if powheg_version.startswith("r"):
        return "CentOS7"
    else:
        return "CentOS8"