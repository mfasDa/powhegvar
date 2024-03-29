#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
INPUTFILE=$3
OUTPUTBASE=$4
PYVERSION=$5
PYTHIAMACRO=$6
VARIATION=$7

PYTHIAFROMROOT=0
INITALICE=0
MACRODIR=$SOURCEDIR/macros/PYTHIA
MACRO=
if [ "$PYTHIAMACRO" == "default" ]; then
	MACRO=$MACRODIR/RunPythia8.C
	echo "Using default macro: $MACRO"
elif [ "$PYTHIAMACRO" == "reweight" ]; then
	MACRO=$MACRODIR/RunPythia8WithWeights.C
	echo "Using reweight macro: $MACRO"
else  
	MACRO=$MACRODIR/$PYTHIAMACRO
fi
if [ "x$(echo $PYVERSION | grep ROOT)" != "x" ]; then
	let "INITALICE=1"
	if [ "$PYTHIAMACRO" == "default" ]; then
		MACRO=$MACRODIR/RunPythia8FromROOT.C
		echo "Using default macro: $MACRO"
	fi
elif [ "x$(echo $PYVERSION | grep FromALICE)" != "x" ]; then
	let "INITALICE=1"
fi

MYHOME=/home/mfasel_alice
if [ "$CLUSTER" == "CADES" ]; then
	source /usr/share/Modules/init/bash
	MYHOME=/home/mfasel_alice
elif [ "$CLUSTER" == "PERLMUTTER" ]; then
	source /usr/share/Modules/init/bash
	MYHOME=/global/homes/m/mfasel
elif [ "$CLUSTER" == "B587" ]; then
	MYHOME=/software/mfasel
fi
source $MYHOME/alice_setenv
if [ $INITALICE -gt 0 ]; then
	ALIENV=`which alienv`
	eval `$ALIENV --no-refresh printenv rootpythia8/latest fastjet/latest`
else
	if [ "$CLUSTER" == "CADES" ]; then
		SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
		module use $SIMSOFT/Modules
		module load ROOT/v6-24-06
		module load PYTHIA/$PYVERSION
		if [ "$PYVERSION" == "v8245" ]; then
			if [ "$PYTHIAMACRO" == "default" ]; then
				MACRO=$MACRODIR/RunPythia8Old.C
				echo "Using default macro: $MACRO"
			fi
		fi
		if [ "$PYVERSION" == "v8186" ]; then
			if [ "$PYTHIAMACRO" == "default" ]; then
				MACRO=$MACRODIR/RunPythia8186.C
				echo "Using default macro: $MACRO"
			fi
		fi
	fi
fi
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
echo "Variation:           $VARIATION"

if [ "$VARIATION" != "NONE" ]; then
	VARIATIONS=(`echo $VARIATION | tr ':' ' '`)
	for VAR in ${VARIATIONS[@]}; do
		VARKEY=$(echo $VAR | cut -d '=' -f 1)
		VARVALUE=$(echo $VAR | cut -d '=' -f 2)
        	echo "Setting variation: $VARKEY = $VARVALUE"

		HASKEY=0
		if [ "$VARKEY" == "PDFSET" ]; then
			export CONFIG_PDFSET=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "TUNE" ]; then
			export CONFIG_TUNE=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "MPI" ]; then
			export CONFIG_MPI=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "PTCUT" ]; then
			export CONFIG_PTCUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "PTCUTCHARGED" ]; then
			export CONFIG_CHPTCUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "PTCUTNEUTRAL" ]; then
			export CONFIG_NEPTCUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "ECUT" ]; then
			export CONFIG_ECUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "ECUTCHARGED" ]; then
			export CONFIG_CHECUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "ECUTNEUTRAL" ]; then
			export CONFIG_NEECUT=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "DECAY" ]; then
			export CONFIG_DECAY=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "JETTYPE" ]; then
			export CONFIG_JETTYPE=$VARVALUE
			let "HASKEY=1"
		fi

		if [ "$VARKEY" == "RECOMBINATIONSCHEME" ]; then
			export CONFIG_RECOMBINATIONSCHEME=$VARVALUE
			let "HASKEY=1"
		fi

		if [ $HASKEY -eq 0 ]; then
			echo "Key $VARKEY not processed"
		fi
	done
fi

CMD=$(printf "root -l -b -q \'%s(\"%s\")\'>> pythia.log" $MACRO $INPUTFILE)
echo "Processing:          $CMD"
eval $CMD
echo "Content of $OUTPUTDIR"
ls -l
echo "Showering $INPUTFILE done"
