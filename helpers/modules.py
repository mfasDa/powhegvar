#! /usr/bin/env python3
import os

def find_powheg_releases() -> list:
    simpath = "/nfs/data/alice-dev/mfasel_alice/simsoft/"
    files = [x for x in os.listdir(os.path.join(simpath, "Modules", "POWHEG"))]
    return files