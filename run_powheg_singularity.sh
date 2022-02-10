#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6

MYHOME=
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/nfs/home/mfasel_alice
    source /opt/rh/devtoolset-7/enable
    SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
    module use $SIMSOFT/Modules/
    module load POWHEG/$POWHEG_VERSION
else 
    MYHOME=/nfs/home/mfasel_alice
    source $MYHOME/alice_setenv
    ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv powheg/latest`
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