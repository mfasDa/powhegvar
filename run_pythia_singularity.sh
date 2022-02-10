#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
INPUTFILE=$3
OUTPUTBASE=$4
PYVERSION=$5
VARIATION=$6
VARVALUE=$7

PYTHIAFROMROOT=0
MACRO=$SOURCEDIR/RunPythia8.C
if [ "x$(echo $PYVERSION | grep ROOT)" != "x" ]; then
	MACRO=$SOURCEDIR/RunPythia8FromROOT.C
	let "PYTHIAFROMROOT=1"
elif [ "x$(echo $PYVERSION | grep FromALICE)" != "x" ]; then
	ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv pythia/latest ROOT/latest fastjet/latest`
fi

MYHOME=/home/mfasel_alice
if [ "$CLUSTER" == "CADES" ]; then
	MYHOME=/home/mfasel_alice
	SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
	module use $SIMSOFT/Modules
	if [ $PYTHIAFROMROOT -gt 0 ]; then 
		module load ROOT/v6-24-06_withPYTHIAv8306
	else 
		module load ROOT/v6-24-06
		module load PYTHIA/$PYVERSION
		if [ "$PYVERSION" == "v8245" ]; then
			MACRO=$SOURCEDIR/RunPythia8Old.C
		fi
		if [ "$PYVERSION" == "v8186" ]; then
			MACRO=$SOURCEDIR/RunPythia8186.C
		fi
	fi
elif [ "$CLUSTER" == "B587" ]; then
	MYHOME=/software/mfasel
fi
source $MYHOME/alice_setenv
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