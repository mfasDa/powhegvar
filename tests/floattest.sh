#! /bin/bash

SOURCEDIR=$PWD

RENSCALES=(0.5 1.0 2.0)
CURRENTWEIGHT=0
for RSCALE in ${RENSCALES[@]}; do
    RSCALEINT=$(echo "$RSCALE * 10 / 1" | bc)
    FACSCALES=(0.5 1.0 2.0)
    for FSCALE in ${FACSCALES[@]}; do
        FSCALEINT=$(echo "$FSCALE * 10 / 1" | bc)
        if [ $RSCALEINT -eq 10 ] && [ $FSCALEINT -eq 10 ]; then
            echo "Skipping muf=$FSCALE ($FSCALEINT), mur=$RSCALE ($RSCALEINT)" 
            continue
        fi
        echo "Processing muf=$FSCALE ($FSCALEINT), mur=$RSCALE ($RSCALEINT)" 
        let "CURRENTWEIGHT++"

        scalename=$(printf "mur%d_muf%d" $RSCALEINT $FSCALEINT)
        namepwginputbkp=$(printf "powheg_scale_%s.input" $scalename)
        logfile=$(printf "pwhg_scale_%s.log" $scalename)
        echo "Using input: $namepwginputbkp, logfile: $logfile"
        
        $SOURCEDIR/prepare_scalereweight.py $SOURCEDIR/powheginputs/powheg_8TeV_CT14_default.input $namepwginputbkp $FSCALE $RSCALE $CURRENTWEIGHT
    done
done