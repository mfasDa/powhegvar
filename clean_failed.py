#! /usr/bin/env python3

import argparse
import logging
import os
import shutil

from helpers import setup_logging

def read_failed_chunks(workdir: str) -> list:
    failed = []
    with open(os.path.join(workdir, "checksummary_pwgevents.log"), "r") as checkreader:
        start_missing_weight = False
        for line in checkreader:
            if start_missing_weight:
                if "----------------------------------------" in line:
                    start_missing_weight = False
                else:
                    file_missweight = line
                    file_missweight = file_missweight.replace(workdir, "").lstrip("/")
                    tokens = file_missweight.split("/")
                    failed.append(int(tokens[0]))
            else:
                if "pwgevents.lhe files with missing weights" in line:
                    start_missing_weight = True
    return sorted(failed)

def report_chunks(chunks: list):
    chunkstring = ""
    first = True
    for chunk in chunks:
        if first:
            first = False
        else:
            first += ", "
        chunkstring += f"{chunk}"
    logging.info("Extracted failed chunks: %s", chunkstring)

def clean_chunk(workdir: str, repository: str, chunk: int, debug: bool = False):
    chunkdir_failed = os.path.join(workdir, "%d" %chunk)
    chunkdir_base = os.path.join(repository, "%d" %chunk)
    logging.info("Cleaning %s", chunkdir_failed)
    if not debug:
        shutil.rmtree(chunkdir_failed)
    logging.info("Copying content from %s to %s", chunkdir_base, chunkdir_failed)
    if not debug:
        shutil.copytree(chunkdir_base, chunkdir_failed)

def process(workdir: str, repo: str, debug: bool = False):
    chunks = read_failed_chunks(workdir)
    report_chunks(chunks)
    for chunk in chunks:
        clean_chunk(workdir, repo, chunk, debug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("clean_failed.py")
    parser.add_argument("workdir", metavar="WORKDIR", type=str, help="Working directory")
    parser.add_argument("repository", metavar="REPOSITORY", type=str, help="Repository with clean data")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()
    process(args.workdir, args.repository, args.debug)