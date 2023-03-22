#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
MINSLOT=$6
OLDGRIDS=$7

SLOT=
let "SLOT=SLURM_ARRAY_TASK_ID+MINSLOT"
echo "Running on host: $HOSTNAME"

CONTAINERCOMMAND=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINERREPO=/nfs/data/alice-dev/mfasel_alice
    if [ "x(echo $POWHEG_VERSION | grep FromALICE)" != "x" ]; then
        # ALICE builds already under CentOS 8
        CONTAINER=mfasel_cc8_alice.simg
    else 
        # Custom POWHEG still using CentOS 7
        CONTAINER=mfasel_cc7_alice.simg
    fi
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
    CONTAINERCOMMAND=$(printf "singularity exec %s %s/%s" "$BINDS" $CONTAINERREPO $CONTAINER)

    module load PE-gnu
    module load singularity
elif [ "$CLUSTER"  == "CORI" ]; then
    module load shifter
    CONTAINERCOMMAND="shifter --module=cvmfs"
fi
EXEC=$SOURCEDIR/run_powheg_singularity.sh

execmd=$(printf "%s %s %s %s %s %s %d %d %d %s" $EXEC $CLUSTER $SOURCEDIR $OUTPUTBASE $POWHEG_VERSION $POWHEG_INPUT $SLOT $OLDGRIDS)
containercmd=""
if [ "x$CONTAINERCOMMAND" != "x" ]; then
    containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "Done ..."