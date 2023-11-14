#! /usr/bin/env python

import socket

def get_cluster():
    hostname = socket.gethostname()
    if "PERLMUTTER" in hostname:
        return "PERLMUTTER"
    elif "or" in hostname:
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