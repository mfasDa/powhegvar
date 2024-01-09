#! /bin/bash

SOURCEDIR=$1
WORKDIR=$2
MINSLOT=$3

export PYTHONPATH=$PYTHONPATH:$SOURCEDIR

SLOT=
let "SLOT=SLURM_ARRAY_TASK_ID+MINSLOT"
SLOTDIR=$(printf "%04d" $SLOT)
echo "Processing slot directory: $SLOTDIR in working directory $WORKDIR"
SLOTWORKINGDIR=$WORKDIR/$SLOTDIR
if [ ! -d $SLOTWORKINGDIR ]; then
    echo "Working directory for slot $SLOT not existing"
    exit 1
fi
cd $SLOTWORKINGDIR
cmd=$(printf "%s/checkPwgevents.py -i %s/pwgevents.lhe" $SOURCEDIR $SLOTWORKINGDIR)
eval $cmd