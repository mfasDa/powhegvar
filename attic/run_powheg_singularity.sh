#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_PROCESS=$4
POWHEG_VERSION=$5
POWHEG_INPUT=$6
MINSLOT=$7
OLDGRIDS=$8
EVENTS=$9

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

RUNSLOT=
let "RUNSLOT=SLOT+MINSLOT"
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR
cmd=$(printf "%s/powheg_runner.py %s %s --slot %s -t %s" $SOURCEDIR $OUTPUTBASE $POWHEG_INPUT $RUNSLOT $POWHEG_PROCESS)
if [ "$OLDGRIDS" != "NONE" ]; then
    cmd=$(printf "%s -g %s" "$cmd" "$OLDGRIDS")
fi
if [ $EVENTS -gt 0 ]; then
    cmd=$(printf "%s -e %d" "$cmd" $EVENTS)
fi
echo "Running: $cmd"
eval $cmd