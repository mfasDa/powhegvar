#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6
REWEIGHTMODE=$7
WEIGHTID=$8
OLDGRIDS=$9

MYHOME=
POWHEG_VERSION_NAME=
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/nfs/home/mfasel_alice
    source /opt/rh/devtoolset-7/enable
    SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
    module use $SIMSOFT/Modules/
    module load POWHEG/$POWHEG_VERSION
    POWHEG_VERSION_NAME=$POWHEG_VERSION
elif [ "$CLUSTER" == "CORI" ]; then
    source /usr/share/Modules/init/bash
    MYHOME=$HOME
    if [ "x(echo $POWHEG_VERSION | grep VO_ALICE)" != "x" ]; then
        eval `/cvmfs/alice.cern.ch/bin/alienv printenv $POWHEG_VERSION`
        POWHEG_VERSION_NAME=$(echo $POWHEG_VERSION | cut -d ":" -f 3)
    else
        source /global/homes/m/mfasel/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv POWHEG/latest` 
        POWHEG_VERSION_NAME=$POWHEG_VERSION
    fi
else 
    MYHOME=/software/mfasel
    if [ "x(echo $POWHEG_VERSION | grep VO_ALICE)" != "x" ]; then
        eval `/cvmfs/alice.cern.ch/bin/alienv printenv $POWHEG_VERSION`
    else
        source $MYHOME/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv POWHEG/latest`
        POWHEG_VERSION_NAME=$POWHEG_VERSION
    fi
fi
module list

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 

JOBDIR=$(printf "%s/POWHEG_%s/%04d" $OUTPUTBASE $POWHEG_VERSION_NAME $SLOT)
if [ ! -d $JOBDIR ]; then mkdir -p $JOBDIR; fi
cd $JOBDIR

cp $POWHEG_INPUT $PWD/powheg.input

if [ "$OLDGRIDS" != "NONE" ]; then
    echo "Using POWHEG grids from $OLDGRIDS"
    if [ -d $OLDGRIDS ]; then
        cp $OLDGRIDS/*.dat $PWD/
        cp $OLDGRIDS/*.top $PWD/
        GRIDFILES=(FlavRegList bornequiv pwhg_checklimits realequiv realequivregions virtequiv)
        for f in ${GRIDFILES[@]}; do
            if [ -f $OLDGRIDS/$f ]; then
                cp $OLDGRIDS/$f $PWD/
            else
                echo "POWHEG grid file $OLDGRIDS/$f missing ..."
            fi
        done
    else
        echo "Grids directory $OLDGRIDS not existing ..."
    fi
else
    echo "Creating new grids ..."
fi

# Set the randomseed
echo "iseed $RANDOM" >> powheg.input

if [ $REWEIGHTMODE -gt 0 ]; then
    if [ ! -f $PWD/pwgevents.lhe ]; then
        echo "Cannot run reweight mode because input file with POWHEG events (pwgevents.lhe) missing"
        exit 1
    fi
    echo "compute_rwgt 1" >> powheg.input
    echo "" >> powheg.input
fi

# Start timing
STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

# The actual POWHEG task
pwhg_main_dijet  >& pwhg.log

# End timing
duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $(($duration / 60)) minutes and $(($duration % 60)) seconds ."