#! /bin/bash

CLUSTER=$1
REPO=$2
ROOTFILE=$3

MYHOME=/home/mfasel_alice
if [ "$CLUSTER" == "CADES" ]; then
	MYHOME=/home/mfasel_alice
elif [ "$CLUSTER" == "PERLMUTTER" ]; then
	MYHOME=/global/homes/m/mfasel
elif [ "$CLUSTER" == "B587" ]; then
	MYHOME=/software/mfasel
fi
source $MYHOME/alice_setenv
ALIENV=`which alienv`
eval `$ALIENV --no-refresh printenv ROOT/latest`
module list

MACRO=$REPO/macros/helpers/splitFile.C
CMD=$(printf "root -l -b -q \'%s(\"%s\")\'" $MACRO $ROOTFILE)
eval $CMD