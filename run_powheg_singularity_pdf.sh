#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
MINSLOT=$6
MINPDF=$7
MAXPDF=$8
MINID=$9

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

RUNSLOT=
let "RUNSLOT=SLOT+MINSLOT"
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR
cmd=$(printf "%s/powheg_runner.py %s %s --slot %s -t dijet --minpdf %s --maxpdf %s --minid %s" $SOURCEDIR $OUTPUTBASE $POWHEG_INPUT $RUNSLOT $MINPDF $MAXPDF $MINID)
echo "Running: $cmd"
eval $cmd