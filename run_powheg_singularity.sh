#! /bin/bash

SOURCEDIR=$1
OUTPUTBASE=$2
POWHEG_VERSION=$3
SLOT=$4

source /opt/rh/devtoolset-7/enable

module use /nfs/data/alice-dev/mfasel_alice/simsoft/Modules/
module load POWHEG/$POWHEG_VERSION

# Setup LHAPDF 
source /nfs/home/mfasel_alice/lhapdf_data_setenv 

JOBDIR=$(printf "%s/POWHEG_%s/%04d" $OUTPUTBASE $POWHEG_VERSION $SLOT)
if [ ! -d $JOBDIR ]; then mkdir -p $JOBDIR; fi
cd $JOBDIR

cp $SOURCEDIR/powheg.input $PWD

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