#! /bin/bash

SOURCEDIR=$1
CLUSTER=$2
POWHEG_VERSION=$3

source $SOURCEDIR/powheg_env.sh $CLUSTER $POWHEG_VERSION
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