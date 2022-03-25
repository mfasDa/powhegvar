#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6
MINPDF=$7
MAXPDF=$8
MINID=$9

MYHOME=
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/nfs/home/mfasel_alice
    source /opt/rh/devtoolset-7/enable
    SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
    module use $SIMSOFT/Modules/
    module load POWHEG/$POWHEG_VERSION
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
module list

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 

DEBUG=0
RUN_DEBUG=1
NO_DEBUG=0

JOBDIR=$(printf "%s/%04d" $OUTPUTBASE $SLOT)
if [ ! -d $JOBDIR ]; then 
    echo "Cannot run reweight mode because input directory does not exist"
    exit 1
fi
cd $JOBDIR

if [ $DEBUG -eq $NO_DEBUG ]; then
    if [ -f powheg.input ]; then rm powheg.input; fi
    cp $POWHEG_INPUT $PWD/powheg_base.input
fi

if [ ! -f $PWD/pwgevents.lhe ]; then
    echo "Cannot run reweight mode because input file with POWHEG events (pwgevents.lhe) missing"
    exit 1
fi

# Start timing
STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

CURRENTPDF=$MINPDF
CURRENTWEIGHT=$MINID
while [ $CURRENTPDF -le $MAXPDF ]; do    
    echo "Processing PDF set: $CURRENTPDF ($CURRENTWEIGHT)" 
    if [ $DEBUG -eq $RUN_DEBUG ]; then
        let "CURRENTPDF++"
        let "CURRENTWEIGHT++"
        continue
    fi

    # set PDF set
    $SOURCEDIR/prepare_pdfreweight.py powheg_base.input powheg.input $CURRENTPDF $CURRENTWEIGHT

    # Set the randomseed
    echo "iseed $RANDOM" >> powheg.input

    # The actual POWHEG task
    echo "Starting POWHEG for PDF $CURRENTPDF"
    pwhg_main_dijet  >& pwhg_pdf$CURRENTPDF.log
    echo "POWHEG for PDFSET $CURRENTPDFPDF done"

    # move output stuff
    mv powheg.input powheg_PDF$CURRENTPDF.input
    mv pwgevents-rwgt.lhe pwgevents.lhe 
    let "CURRENTPDF++"
    let "CURRENTWEIGHT++"
done

# End timing
duration=$SECONDS
ENDSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job ends: $ENDSTRING" 
echo "Job took $(($duration / 3600)) hours, $(($duration / 60)) minutes and $(($duration % 60)) seconds ."