#! /bin/bash

CLUSTER=$1
POWHEG_VERSION=$2

echo "Initialise POWHEG on CLUSTER:    $CLUSTER"
echo "Request POWHEG version:          $POWHEG_VERSION"

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