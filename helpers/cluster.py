#! /usr/bin/env python

import socket
import os

def get_cluster():
    nersc_host = os.getenv("NERSC_HOST")
    if nersc_host != None and  len(nersc_host):
        if nersc_host == "perlmutter":
            return "PERLMUTTER"
    else:
        hostname = socket.gethostname()
        if "or" in hostname:
            return "CADES"
        elif "pc" in hostname:
            return "B587"

def get_default_partition(cluster: str):
    if cluster == "CADES":
        return "high_mem_cd"
    elif cluster == "PERLMUTTER":
        return "shared"
    elif cluster == "B587":
        return "long"

def get_fast_partition(cluster: str):
    if cluster == "CADES":
        return "high_mem_cd"
    elif cluster == "PERLMUTTER":
        return "shared"
    elif cluster == "B587":
        return "short"