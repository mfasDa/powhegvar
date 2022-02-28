#! /bin/bash

CLUSTER=$1
SOURCEDIR=$2
OUTPUTBASE=$3
POWHEG_VERSION=$4
POWHEG_INPUT=$5
SLOT=$6
MINPDF=$7
MAXPDF=$8

MYHOME=
if [ "$CLUSTER" == "CADES" ]; then
    MYHOME=/nfs/home/mfasel_alice
    source /opt/rh/devtoolset-7/enable
    SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
    module use $SIMSOFT/Modules/
    module load POWHEG/$POWHEG_VERSION
else 
    MYHOME=/nfs/home/mfasel_alice
    source $MYHOME/alice_setenv
    ALIENV=`which alienv`
    eval `$ALIENV --no-refresh printenv powheg/latest`
fi
module list

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 

JOBDIR=$(printf "%s/%04d" $OUTPUTBASE $SLOT)
if [ ! -d $JOBDIR ]; then mkdir -p $JOBDIR; fi
cd $JOBDIR

if [ -f powheg.input ]; then rm powheg.input; fi
cp $POWHEG_INPUT $PWD/powheg_base.input

if [ ! -f $PWD/pwgevents.lhe ]; then
    echo "Cannot run reweight mode because input file with POWHEG events (pwgevents.lhe) missing"
    exit 1
fi

# Start timing
STARTSTRING=$(date "+%d.%m.%Y %H:%M:%S")
echo "Job start: $STARTSTRING" 
SECONDS=0

CURRENTPDF=$MINPDF
CURRENTWEIGHT=1
while [ $CURRENTPDF -le $MAXPDF ]; do    
    echo "Processing PDF set: $CURRENTPDF ($CURRENTWEIGHT)" 
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