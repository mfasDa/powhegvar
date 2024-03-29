#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
VARIATION=$4
VARVALUE=$5

SLOT=$SLURM_ARRAY_TASK_ID

CONTAINERREPO=
CONTAINER=
BINDS=
if [ "$CLUSTER" == "CADES" ]; then
    CONTAINERREPO=/nfs/data/alice-dev/mfasel_alice
    CONTAINER=mfasel_cc7_alice.simg
    BINDS="-B /home:/home -B /nfs:/nfs -B /lustre:/lustre"

    module load PE-gnu
    module load singularity
fi
EXEC=$SOURCEDIR/run_pythia_singularity_original.sh


STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

FILELIST=$OUTPUTBASE/filelists/pwhgin$SLOT.txt
echo "Processing files from $FILELIST"
cat $FILELIST
while read INPUTFILE; do
    execmd=$(printf "%s %s %s %s %s %s %s" $EXEC $CLUSTER $SOURCEDIR $INPUTFILE $OUTPUTBASE $VARIATION $VARVALUE)
    containercmd=
    if [ "x$CONTAINER" != "x" ]; then
        containercmd=$(printf "singularity exec %s %s/%s %s" "$BINDS" $CONTAINERREPO $CONTAINER "$execmd")
    else
        containercmd=$execmd
    fi

    echo "Running $containercmd"
    eval $containercmd
    echo "File done ..."
done < $FILELIST

duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $(($duration / 60)) minutes and $(($duration % 60)) seconds ."