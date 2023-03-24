#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
MINSLOT=$6

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

RUNSLOT=
let "RUNSLOT=SLOT+MINSLOT"
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR
cmd=$(printf "%s/powheg_runner.py %s %s --slot %s -t dijet -s --minid 0" $SOURCEDIR $OUTPUTBASE $POWHEG_INPUT $RUNSLOT)
echo "Running: $cmd"
eval $cmd