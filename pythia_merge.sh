#! /bin/bash
CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
ROOTFILE=$4

CONTAINER=
BINDS=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINER=/nfs/home/mfasel_alice/mfasel_cc7_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"

    module load PE-gnu
    module load singularity
fi
EXEC=$SOURCEDIR/run_merge_singularity.sh


execmd=$(printf "%s %s %s %s" $EXEC $CLUSTER $OUTPUTBASE $ROOTFILE)
containercmd=
if [ "x$CONTAINER" != "x" ]; then
    containercmd=$(printf "singularity exec %s %s %s" "$BINDS" $CONTAINER "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "File done ..."