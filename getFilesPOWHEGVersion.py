#! /usr/bin/env python3

import os
import sys

sourcedir = "/nfs/data/alice-dev/mfasel_alice/simsoft/source/POWHEG"

def find_all_files(powhegversion: str):
    
    outputfiles = []
    pwgbase = os.path.join(sourcedir, powhegversion)
    for root, dirs, files in os.walk(pwgbase):
        for f in files:
            fullpath = os.path.join(root, f)
            fullpath = fullpath.replace(pwgbase, "")
            fullpath = fullpath.lstrip("/")
            outputfiles.append(fullpath)
    return sorted(outputfiles)

def store_pwhgfiles(powhegversion: str):
    repo = os.path.dirname(os.path.abspath(sys.argv[0]))
    outputdir = os.path.join(repo, "powhegfiles") 
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)
    with open(os.path.join("{}.txt".format(powhegversion)), "w") as versionwriter:
        for fl in find_all_files(powhegversion):
            versionwriter.write("{}\n".format(fl))
        versionwriter.close()

if __name__ == "__main__":
    version = sys.argv[1]
    versions = [x for x in os.listdir(sourcedir) if "powheg" in x]
    if version == "all":
        for version in versions:
            store_pwhgfiles(version)
    else:
        if version in versions:
            store_pwhgfiles(version)
        else:
            print("Requested POWHEG version {} not found".format(version))