#! /bin/bash
CLUSTER=$1
SOURCEDIR=$2
WORKDIR=$3
ROOTFILE=$4

CONTAINERCOMMAND=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINERREPO=/nfs/data/alice-dev/mfasel_alice
    CONTAINER=mfasel_cc7_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"
    CONTAINERCOMMAND=$(printf "singularity exec %s %s/%s" "$BINDS" $CONTAINERREPO $CONTAINER)

    module load PE-gnu
    module load singularity
elif [ "$CLUSTER"  == "PERLMUTTER" ]; then
    module load shifter
    CONTAINERCOMMAND="shifter"
fi
EXEC=$SOURCEDIR/run_split_singularity.sh

FILES=($(find $WORKDIR -name $FILENAME))
for INFILE in ${FILES[@]}; do
    echo "Splitting $INFILE"
    execmd=$(printf "%s %s %s %s" $EXEC $CLUSTER $SOURCEDIR $INFILE)
    containercmd=
    if [ "x$CONTAINERCOMMAND" != "x" ]; then
        containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")    
    else
        containercmd=$execmd
    fi

    echo "Running $containercmd"
    eval $containercmd
    echo "File done ..."
done