#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
SLOT=$5
STAGE=$6
XGRID_ITER=$7

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION

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
pwhg_main_dijet << EOF
$SLOT 
EOF
#>& $logfile

# End timing
duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $((($duration / 60) % 60)) minutes and $(($duration % 60)) seconds ."