#! /bin/bash

SOURCEDIR=$1
WORKDIR=$2

cmd=$(printf "%s/scan_check_pwgevents.py %s &> %s/checksummary_pwgevents.log" $SOURCEDIR $WORKDIR $WORKDIR)
eval $cmd