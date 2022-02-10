#!/bin/sh
date

mkdir -p $2

mv * $2/

cd $2/

echo "Executing run $2 on" `hostname` "in $PWD"

source /afs/cern.ch/work/h/hahassan/env.sh

echo "iseed $RANDOM" >> powheg.input

#pwhg_main_hvq  >& pwhg.log
pwhg_main_dijet  >& pwhg.log

date

export CONFIG_SEED=$RANDOM

root.exe -b > ana.log 2> ana.err << EOF

gSystem->Load("libfastjet");
.x ./RunPythia8.C++(100000)
.q
EOF

date

WORKDIR="/eos/user/h/hahassan/POWHEG/pp13TeVdijet_CT14nlo/"

mkdir -p $WORKDIR

mv _condor_stdout _condor_stderr tmp/ var/ condor_exec.exe ../
