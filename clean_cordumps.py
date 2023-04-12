#! /usr/bin/env python3

import argparse
import os

def process_slotdir(slotdir: str):
    for fl in os.listdir(slotdir):
        if "core." in fl:
            print(f"Removing {fl} in {slotdir}")
            os.remove(os.path.join(slotdir, fl))

def find_slots(workdir: str) -> list:
    return [x for x in os.listdir(workdir) if x.isdigit()]

if __name__ == "__main__":
    parser = argparse.ArgumentParser("clean_coredumps.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    args = parser.parse_args()

    workdir = os.path.abspath(args.workdir)
    for slot in find_slots(workdir):
        process_slotdir(os.path.join(workdir, slot))