#! /bin/bash

SOURCEDIR=$1
SLOTWORKINGDIR=$2

export PYTHONPATH=$PYTHONPATH:$SOURCEDIR

echo "Processing slot directory: $SLOTWORKINGDIR"
if [ ! -d $SLOTWORKINGDIR ]; then
    echo "Slot directory not existing"
    exit 1
fi
cd $SLOTWORKINGDIR
cmd=$(printf "%s/checkPwgevents.py -i %s/pwgevents.lhe" $SOURCEDIR $SLOTWORKINGDIR)
eval $cmd