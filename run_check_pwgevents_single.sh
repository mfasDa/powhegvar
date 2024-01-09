#! /bin/bash

SOURCEDIR=$1
WORKDIR=$2

export PYTHONPATH=$PYTHONPATH:$SOURCEDIR

SLOTS=($(ls -1 $WORKDIR | grep -E "[0-9]+"))

for SLOTDIR in ${SLOTS[@]}; do
    echo "Processing slot directory: $SLOTDIR in working directory $WORKDIR"
    SLOTWORKINGDIR=$WORKDIR/$SLOTDIR
    if [ ! -d $SLOTWORKINGDIR ]; then
        echo "Working directory for slot $SLOTDIR not existing"
        continue
    fi
    cd $SLOTWORKINGDIR
    cmd=$(printf "%s/checkPwgevents.py -i %s/pwgevents.lhe" $SOURCEDIR $SLOTWORKINGDIR)
    eval $cmd
done
cd $WORKDIR