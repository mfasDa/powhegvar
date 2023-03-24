#! /bin/bash

SCRIPT=`readlink -f $0`
REPO=`dirname $SCRIPT`
EXE=$REPO/toptoroot.py

eval `alienv --no-refresh printenv ROOT/latest`

WORKDIR=$1
BASEDIR=$PWD
cd $WORKDIR
chunks=($(ls -1 $WORKDIR))
for chunk in ${chunks[@]}; do
    cd $WORKDIR/$chunk
    topfiles=($(ls -1 | grep top))
    for fl in ${topfiles[@]}; do
        $EXE $fl
    done
    ROOTHISTOS=($(ls -1 | grep root))
    mergecmd="hadd -f powheghists.root"
    for rh in ${ROOTHISTOS[@]}; do
        mergecmd=$(printf "%s %s" "$mergecmd" "$rh")
    done
    eval $mergecmd
    for rh in ${ROOTHISTOS[@]}; do
        rm $rh
    done

    cd $WORKDIR
done
cd $BASEDIR
