#! /bin/bash

SOURCEDIR=$1
WORKDIR=$2

cmd=$(print "%s/scan_check_pwgevents.py %s &> %s/checksummary_pwgevents.log" $SOURCEDIR $WORKDIR $WORKDIR)
eval $cmd