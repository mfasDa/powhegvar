#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
INPUTFILE=$3
OUTPUTBASE=$4
VARIATION=$5
VARVALUE=$6

MACRO=$SOURCEDIR/Hadi_original/RunPythia8.C

MYHOME=/home/mfasel_alice
if [ "$CLUSTER" == "CADES" ]; then
	MYHOME=/home/mfasel_alice
elif [ "$CLUSTER" == "B587" ]; then
	MYHOME=/software/mfasel
fi
source $MYHOME/alice_setenv
ALIENV=`which alienv`
eval `$ALIENV --no-refresh printenv rootpythia8/latest fastjet/latest`
module list
source $MYHOME/lhapdf_data_setenv
export CONFIG_SEED=$RANDOM

INPUTDIR=`dirname $INPUTFILE`
SLOT=`basename $INPUTDIR`
OUTPUTDIR=$OUTPUTBASE/$SLOT
if [ ! -d $OUTPUTDIR ]; then mkdir -p $OUTPUTDIR; fi
cd $OUTPUTDIR

echo "Input file:          $INPUTFILE"
echo "Output directory:    $OUTPUTDIR"
echo "Macro:               $MACRO"

if [ "$VARIATION" == "PDFSET" ]; then
	export CONFIG_PDFSET=$VARVALUE
fi

if [ "$VARIATION" == "TUNE" ]; then
	export CONFIG_TUNE=$VARVALUE
fi

if [ "$VARIATION" == "MPI" ]; then
	export CONFIG_MPI=$VARVALUE
fi


CMD=$(printf "root -l -b -q \'%s(\"%s\")\'>> pythia.log" $MACRO $INPUTFILE)
echo "Processing:          $CMD"
eval $CMD
echo "Content of $OUTPUTDIR"
ls -l
echo "Showering $INPUTFILE done"