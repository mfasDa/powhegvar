#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6

# Run job only if the jobdir exists AND contains a valid pwgevents.lhe
JOBDIR=$(printf "%s/%04d" $OUTPUTBASE $SLOT)
if [ ! -d $JOBDIR ]; then 
    echo "Cannot run reweight mode because input directory does not exist"
    exit 1
elif [ ! -f $JOBDIR/pwgevents.lhe ]; then
    echo "Cannot run reweight mode because input file with POWHEG events (pwgevents.lhe) missing"
    exit 1
fi 
cd $JOBDIR
echo "Running in job directory: $JOBDIR"

MYHOME=
DOMODULE=1
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/home/mfasel_alice
    if [ "x(echo $POWHEG_VERSION | grep FromALICE)" != "x" ]; then
        source $MYHOME/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv POWHEG/latest` 
        alienv list
        let "DOMODULE=0"
    else 
        source /opt/rh/devtoolset-10/enable
        SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
        module use $SIMSOFT/Modules/
        module load POWHEG/$POWHEG_VERSION
    fi
elif [ "$CLUSTER" == "CORI" ]; then
    source /usr/share/Modules/init/bash
    MYHOME=$HOME
    if [ "x(echo $POWHEG_VERSION | grep VO_ALICE)" != "x" ]; then
        eval `/cvmfs/alice.cern.ch/bin/alienv printenv $POWHEG_VERSION`
    else
        # Take local build from Markus
        source /global/homes/m/mfasel/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv POWHEG/latest` 
    fi
else 
    MYHOME=/software/mfasel
    source $MYHOME/alice_setenv
    ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv POWHEG/latest`
fi
if [ $DOMODULE -gt 0 ]; then
    module list
fi

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 

DEBUG=0
RUN_DEBUG=1
NO_DEBUG=0

if [ $DEBUG -eq $NO_DEBUG ]; then
    if [ -f powheg.input ]; then rm powheg.input; fi
    cp $POWHEG_INPUT $PWD/powheg_base.input
fi

# Start timing
STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

echo Directory content before processing:
ls -l

SCALES=(0.5 1.0 2.0)
SCALESINT=(5 10 20)
CURRENTWEIGHT=0
for INDEXREN in `seq 0 2`; do
    RSCALE=${SCALES[$INDEXREN]}
    RSCALEINT=${SCALESINT[$INDEXREN]} # Convert to int for later processing at bash level
    for INDEXFAC in `seq 0 2`; do
        FSCALE=${SCALES[$INDEXFAC]}
        FSCALEINT=${SCALESINT[$INDEXFAC]} # Convert to int for later processing at bash level

        # Do not process muf = mur = 1 as it is the default configuration
        if [ $RSCALEINT -eq 10 ] && [ $FSCALEINT -eq 10 ]; then
            echo "Skipping muf=$FSCALE ($FSCALEINT), mur=$RSCALE ($RSCALEINT)" 
            continue
        fi
        
        echo "=========================================================================================="
        echo "Processing muf=$FSCALE ($FSCALEINT), mur=$RSCALE ($RSCALEINT) (ID $CURRENTWEIGHT)" 
        if [ $DEBUG -eq $RUN_DEBUG ]; then
            let "CURRENTWEIGHT++"
            continue
        fi

        # create configuration for scale reweight
        $SOURCEDIR/prepare_scalereweight.py powheg_base.input powheg.input $FSCALE $RSCALE $CURRENTWEIGHT

        # Set the randomseed
        echo "iseed $RANDOM" >> powheg.input

        # Names for files with dedicated combination of factorisation and renormalisation scale
        scalename=$(printf "mur%d_muf%d" $RSCALEINT $FSCALEINT)
        namepwginputbkp=$(printf "powheg_scale_%s.input" $scalename)
        logfile=$(printf "pwhg_scale_%s.log" $scalename)

        # The actual POWHEG task
        echo "Starting POWHEG for muf=$FSCALE, mur=$RSCALE"
        ls -l
        if [ -f pwgevents-rwgt.lhe ]; then
            echo "Found unexpected pwgevents-rwgt.lhe, reweighting will go into error"
        fi
        pwhg_main_dijet &> $logfile
        echo "POWHEG for muf $CURRENTPDFPDF done"

        # move output stuff
        mv powheg.input $namepwginputbkp
        mv pwgevents-rwgt.lhe pwgevents.lhe 
        let "CURRENTWEIGHT++"
        echo "=========================================================================================="
    done
done

# End timing
duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $(($duration % 3600)) minutes and $(($duration % 60)) seconds ."