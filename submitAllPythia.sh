#! /bin/bash
INPUTBASE=$1
OUTPUTBASE=$2
POWHEG_VERSION=$3
VARIATION=$4

SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
MODULEDIR=$SIMSOFT/Modules/PYTHIA
PYVERSIONS=(FromROOT v8245 v8306)
#PYVERSIONS=(v8245 v8306)

SCRIPT=`readlink -f $0`
SOURCEDIR=`dirname $SCRIPT`
SUBMITTER=$SOURCEDIR/submit_pythia.py

POWHEGDIR=$INPUTBASE/$POWHEG_VERSION
OUTPUTDIR=$OUTPUTBASE/$POWHEG_VERSION

#CMD=$(printf "%s/submit_pythia.py %s %s FromROOT -n 5" $SOURCEDIR $POWHEGDIR $OUTPUTDIR)
#eval $CMD

for VER in ${PYVERSIONS[@]}; do
    echo "Submitting PYTHIA version: $VER"
    CMD=$(printf "%s/submit_pythia.py %s %s %s -v %s -n 5" $SOURCEDIR $POWHEGDIR $OUTPUTDIR $VER $VARIATION)
    eval $CMD
done