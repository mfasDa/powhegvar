#! /bin/bash

REPO=$1
WORKDIR=$2
GRIDFILE=$3

export PYTHONPATH=$PYTHONPATH:$REPO

cmd=$(printf "%s/pack_grids_production.py %s" $REPO $WORKDIR)
echo "Executing: $cmd"
eval $cmd
echo "Done ..."