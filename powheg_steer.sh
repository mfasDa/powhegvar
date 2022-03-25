#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
REWEIGHTMODE=$6
WEIHGTID=$7
OLDGRIDS=$8

SLOT=$SLURM_ARRAY_TASK_ID

CONTAINERCOMMAND=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINER=/nfs/home/mfasel_alice/mfasel_cc7_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
    CONTAINERCOMMAND=$(printf "singularity exec %s %s" "$BINDS" $CONTAINER)

    module load PE-gnu
    module load singularity
elif [ "$CLUSTER"  == "CORI" ]; then
    module load shifter
    CONTAINERCOMMAND="shifter --module=cvmfs"
fi
EXEC=$SOURCEDIR/run_powheg_singularity.sh

execmd=$(printf "%s %s %s %s %s %s %d %d %d %s" $EXEC $CLUSTER $SOURCEDIR $OUTPUTBASE $POWHEG_VERSION $POWHEG_INPUT $SLOT $REWEIGHTMODE $WEIHGTID $OLDGRIDS)
containercmd=""
if [ "x$CONTAINERCOMMAND" != "x" ]; then
    containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "Done ..."