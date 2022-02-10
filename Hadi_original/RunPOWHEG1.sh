#!/bin/sh
date

WORKDIR="/eos/user/h/hahassan/POWHEG/pp13TeVdijet_CT14nlo/$2"

cd $WORKDIR

echo "Executing run $2 on" `hostname` "in $PWD"

source /afs/cern.ch/work/h/hahassan/env.sh

cp /afs/cern.ch/user/h/hahassan/powheg/dijet13TeV_wgt/RunPythia8.C .

export CONFIG_SEED=$RANDOM

#export CONFIG_SEED=`awk '/^iseed/{print $NF}' powheg.input`

root.exe -b > ana.log 2> ana.err << EOF

gSystem->Load("libfastjet");
.x ./RunPythia8.C++(100000)
.q
EOF

date
