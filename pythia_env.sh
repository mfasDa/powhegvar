#! /bin/bash

CLUSTER=$1
PYTHIA_VERSION=$2

echo "Initialise POWHEG on CLUSTER:    $CLUSTER"
echo "Request PYTHIA version:          $PYTHIA_VERSION"

MYHOME=
DOMODULE=1
if [ "$CLUSTER" == "CADES" ]; then
    echo "Setup environment for CADES ..."     
    MYHOME=/home/mfasel_alice
    if [ "x$(echo $PYTHIA_VERSION | grep FromALICE)" != "x" ]; then
        echo "Using PYTHIA from alidist ..."
        source $MYHOME/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv rootpythia8/latest fastjet/latest` 
        alienv list
        let "DOMODULE=0"
    else 
        echo "Using PYTHIA from simsoft ..."
        source /opt/rh/devtoolset-10/enable
        SIMSOFT=/nfs/data/alice-dev/mfasel_alice/simsoft
        module use $SIMSOFT/Modules/
        module load PYTHIA/$PYTHIA_VERSION
    fi
elif [ "$CLUSTER" == "PERLMUTTER" ]; then
    echo "Setup environment for Perlmutter ..."     
    source /usr/share/Modules/init/bash
    MYHOME=$HOME
    if [ "x$(echo $PYTHIA_VERSION | grep "VO_ALICE")" != "x" ]; then
        echo "Using PYTHIA from cvmfs ..."
        eval `/cvmfs/alice.cern.ch/bin/alienv printenv $PYTHIA_VERSION`
    else
        # Take local build from Markus
        echo "Using PYTHIA from alidist ..."
        source /global/homes/m/mfasel/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv rootpythia8/latest fastjet/latest` 
        alienv list 
    fi
    let "DOMODULE=0"
else 
    echo "Setup environment on 587 cluster ..."
    MYHOME=/software/mfasel
    if [ "x$(echo $PYTHIA_VERSION | grep "VO_ALICE")" != "x" ]; then
        echo "Using PYTHIA from cvmfs ..."
        eval `/cvmfs/alice.cern.ch/bin/alienv printenv $PYTHIA_VERSION`
    else
        # Take local build from Markus
        echo "Using PYTHIA from alidist ..."
        source $MYHOME/alice_setenv
        ALIENV=`which alienv`
        eval `$ALIENV --no-refresh printenv rootpythia8/latest fastjet/latest` 
    fi
    let "DOMODULE=0"
fi
if [ $DOMODULE -gt 0 ]; then
    module list
fi

# Setup LHAPDF 
source $MYHOME/lhapdf_data_setenv 