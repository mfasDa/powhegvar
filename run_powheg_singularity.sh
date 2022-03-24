#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6
REWEIGHTMODE=$7
WEIGHTID=$8

MYHOME=
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/nfs/home/mfasel_alice
    source /opt/rh/devtoolset-7/enable
    SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
    module use $SIMSOFT/Modules/
    module load POWHEG/$POWHEG_VERSION
elif [ "$CLUSTER" == "CORI" ]; then
    source /usr/share/Modules/init/bash
    MYHOME=/global/homes/m/mfasel
    source $MYHOME/alice_setenv
    ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv POWHEG/latest` 
else 
    MYHOME=/software/mfasel
    source $MYHOME/alice_setenv
    ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv POWHEG/latest`
fi
module list

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 

JOBDIR=$(printf "%s/POWHEG_%s/%04d" $OUTPUTBASE $POWHEG_VERSION $SLOT)
if [ ! -d $JOBDIR ]; then mkdir -p $JOBDIR; fi
cd $JOBDIR

cp $POWHEG_INPUT $PWD/powheg.input

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