#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
SLOT=$5
STAGE=$6
XGRID_ITER=$7

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

cd $OUTPUTBASE

# Start timing
STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

# The actual POWHEG task
logfile=$(printf "powheg_stage_%d" $STAGE)
if [ $XGRID_ITER -gt 0 ]; then
    logfile=$(printf "%s_xgriditer%d" "$logfile" $XGRID_ITER)
fi
logfile=$(printf "%s_slot%d.log" "$logfile" $SLOT)
pwhg_main_dijet $SLOT  >& pwhg.log

# End timing
duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $(($duration / 60)) minutes and $(($duration % 60)) seconds ."