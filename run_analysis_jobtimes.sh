#! /bin/bash

SOURCEDIR=$1
WORKDIR=$2
PATTERN=$3
OUTPUTFILE=$4
TAG=${5:-""}

module load PE-gnu

source /home/mfasel_alice/python_venv/matplot_env/bin/activate
export $PYTHONPATH=$PYTHONPATH:$SOURCEDIR

cmd=$(printf "%s/analyse_times.py %s %s %s/%s" $SOURCEDIR $WORKDIR $PATTERN $WORKDIR $OUTPUTFILE)
if [ "x$(echo $TAG)" != "x" ]; then
    cmd=$(printf "%s -t %s" "$cmd" "$TAG")
fi
echo "Running: $cmd"
eval $cmd

deactivate