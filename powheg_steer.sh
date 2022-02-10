#! /bin/bash

SOURCEDIR=$1
OUTPUTBASE=$2
POWHEG_VERSION=$3

SLOT=$SLURM_ARRAY_TASK_ID

CONTAINER=/nfs/home/mfasel_alice/mfasel_cc7_alice.simg
BINDS="-B /nfs:/nfs -B /lustre:/lustre"
EXEC=$SOURCEDIR/run_powheg_singularity.sh

module load PE-gnu
module load singularity

execmd=$(printf "%s %s %s %s %d" $EXEC $SOURCEDIR $OUTPUTBASE $POWHEG_VERSION $SLOT)
containercmd=$(printf "singularity exec %s %s %s" "$BINDS" $CONTAINER "$execmd")

echo "Running $containercmd"
eval $containercmd
echo "Done ..."