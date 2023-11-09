#! /bin/bash

WORKDIR=$1
STAGECONFIG=$2
STAGESEEDS=$3

if [ ! -d $WORKDIR ]; then
    mkdir -p $WORKDIR
fi

if [ "$STAGECONFIG" != "default" ]; then
    echo "Installing stage configuration: $STAGECONFIG"
    cp $STAGECONFIG $WORKDIR/powheg.input
fi
if [ "$STAGESEEDS" != "default" ]; then
    echo "Installing stage seeds: $STAGESEEDS"
    cp $STAGESEEDS $WORKDIR/pwgseeds.dat
fi