#! /bin/bash

POWHEG=$1
INPUTDIR=/lustre/or-scratch/cades-birthright/mfasel_alice/POWHEGvar/production/v1_CT14nlo
OUTPUTDIR=/lustre/or-scratch/cades-birthright/mfasel_alice/POWHEGvar/production/v1_CT14nlo/Pythia_v1
/home/mfasel_alice/work/POWHEGvar/submitAllPythia.sh  $INPUTDIR $OUTPUTDIR $POWHEG