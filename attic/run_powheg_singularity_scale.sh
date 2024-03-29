#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_PROCESS=$4
POWHEG_VERSION=$5
POWHEG_INPUT=$6
MINSLOT=$7

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

RUNSLOT=
let "RUNSLOT=SLOT+MINSLOT"
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR
cmd=$(printf "%s/powheg_runner.py %s %s --slot %s -t %s -s --minid 0" $SOURCEDIR $OUTPUTBASE $POWHEG_INPUT $POWHEG_PROCESS $RUNSLOT)
echo "Running: $cmd"
eval $cmd