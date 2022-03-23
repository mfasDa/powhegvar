#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
PYVERSION=$4
PYTHIAMACRO=$5
VARIATION=$6

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
    CONTAINERCOMMAND="shifter"
fi
EXEC=$SOURCEDIR/run_pythia_singularity.sh


STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

FILELIST=$OUTPUTBASE/filelists/pwhgin$SLOT.txt
echo "Processing files from $FILELIST"
cat $FILELIST
while read INPUTFILE; do
    execmd=$(printf "%s %s %s %s %s %s %s %s" $EXEC $CLUSTER $SOURCEDIR $INPUTFILE $OUTPUTBASE $PYVERSION $PYTHIAMACRO $VARIATION)
    containercmd=
    if [ "x$CONTAINERCOMMAND" != "x" ]; then
        containercmd=$(printf "%s %s" "$CONTAINERCOMMAND" "$execmd")
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
