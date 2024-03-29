#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
STAGE=$5
XGRID_ITER=$6

SLOT=$SLURM_ARRAY_TASK_ID

CONTAINERCOMMAND=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINERREPO=/nfs/data/alice-dev/mfasel_alice
    CONTAINER=
    if [ "$POWHEG_VERSION" == "FromALICE" ]; then
        CONTAINER=mfasel_cc8_alice.simg
    else
        CONTAINER=mfasel_cc7_alice.simg
    fi
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
    CONTAINERCOMMAND=$(printf "singularity exec %s %s/%s" "$BINDS" $CONTAINERREPO $CONTAINER)

    module load PE-gnu
    module load singularity
elif [ "$CLUSTER"  == "PERLMUTTER" ]; then
    module load shifter
    CONTAINERCOMMAND="shifter --module=cvmfs"
fi
EXEC=$SOURCEDIR/run_powheg_stage_singularity.sh

execmd=$(printf "%s %s %s %s %s %d %d %d" $EXEC $CLUSTER $SOURCEDIR $OUTPUTBASE $POWHEG_VERSION $SLOT $STAGE $XGRID_ITER)
containercmd=""
if [ "x$CONTAINER" != "x" ]; then
    containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "Done ..."