#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
STAGE=$5
XGRID_ITER=$6

SLOT=$SLURM_ARRAY_TASK_ID

CONTAINER=
BINDS=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINER=/nfs/home/mfasel_alice/mfasel_cc7_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"

    module load PE-gnu
    module load singularity
fi
EXEC=$SOURCEDIR/run_powheg_stage_singularity.sh

execmd=$(printf "%s %s %s %s %s %d %d %d" $EXEC $CLUSTER $SOURCEDIR $OUTPUTBASE $POWHEG_VERSION $SLOT $STAGE $XGRID_ITER)
containercmd=""
if [ "x$CONTAINER" != "x" ]; then
    containercmd=$(printf "singularity exec %s %s %s" "$BINDS" $CONTAINER "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "Done ..."