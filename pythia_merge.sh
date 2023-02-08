#! /bin/bash
CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
ROOTFILE=$4

CONTAINERCOMMAND=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINERREPO=/nfs/data/alice-dev/mfasel_alice
    CONTAINER=mfasel_cc8_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
    CONTAINERCOMMAND=$(printf "singularity exec %s %s/%s" "$BINDS" $CONTAINERREPO $CONTAINER)

    module load PE-gnu
    module load singularity
elif [ "$CLUSTER"  == "CORI" ]; then
    module load shifter
    CONTAINERCOMMAND="shifter"
fi
EXEC=$SOURCEDIR/run_merge_singularity.sh


execmd=$(printf "%s %s %s %s" $EXEC $CLUSTER $OUTPUTBASE $ROOTFILE)
containercmd=
if [ "x$CONTAINERCOMMAND" != "x" ]; then
    containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")
else
    containercmd=$execmd
fi

echo "Running $containercmd"
eval $containercmd
echo "File done ..."