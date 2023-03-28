#! /usr/bin/env python3

import os

def range_jobdirs(workdir: str) -> tuple:
    jobdirs = sorted([x for x in os.listdir(workdir) if os.path.isdir(os.path.join(workdir, x)) and x.isdigit()])
    if not len(jobdirs):
        return (-1, -1)
    return (int(jobdirs[0]), int(jobdirs[len(jobdirs) -1]))

def find_index_of_input_file_range(workdir: str) -> int:
    pwgdirs = sorted([int(x) for x in os.listdir(workdir) if os.path.isfile(os.path.join(workdir, x, "pwgevents.lhe"))])
    if not len(pwgdirs):
        return (-1, -1)
    return (pwgdirs[0], pwgdirs[len(pwgdirs)-1]) 