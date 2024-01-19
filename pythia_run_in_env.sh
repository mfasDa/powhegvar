#! /bin/bash

SOURCEDIR=$1
CLUSTER=$2
PYTHIA_VERSION=$3

source $SOURCEDIR/pythia_env.sh $CLUSTER $PYTHIA_VERSION
export PYTHONPATH=$PYTHONPATH:$SOURCEDIR

argindex=0
RUNCMD=""
for i in $@; do
    let "argindex++"
    if [ $argindex -le 3 ]; then
        continue
    fi
    if [ "x$RUNCMD" == "x" ]; then
        RUNCMD=$i
    else
        RUNCMD=$(printf "%s %s" "$RUNCMD" "$i")
    fi
done
echo "Running in environment: $RUNCMD"
eval $RUNCMD