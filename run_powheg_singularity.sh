#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
MINSLOT=$6
OLDGRIDS=$7

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

RUNSLOT=
let "RUNSLOT=SLOT+MINSLOT"
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR
cmd=$(printf "%s/powheg_runner.py %s %s --slot %s -t dijet" $SOURCEDIR $OUTPUTBASE $POWHEG_INPUT $RUNSLOT)
if [ "$OLDGRIDS" != "NONE" ]; then
    cmd=$(printf "%s -g %s" "$cmd" "$OLDGRIDS")
fi
echo "Running: $cmd"
eval $cmd