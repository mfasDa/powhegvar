#! /bin/bash

CLUSTER=$1
OUTPUTBASE=$2
ROOTFILE=$3

MYHOME=/home/mfasel_alice
if [ "$CLUSTER" == "CADES" ]; then
	MYHOME=/home/mfasel_alice
elif [ "$CLUSTER" == "CORI" ]; then
	MYHOME=/global/homes/m/mfasel
elif [ "$CLUSTER" == "B587" ]; then
	MYHOME=/software/mfasel
fi
source $MYHOME/alice_setenv
ALIENV=`which alienv`
eval `$ALIENV --no-refresh printenv ROOT/latest`
module list

FILEBASE=$(echo $ROOTFILE | cut -d '.' -f1)
MERGEFILE=$(printf "%s_merged.root" $FILEBASE)

OUTPUTFILE=$OUTPUTBASE/$MERGEFILE
if [ -f $OUTPUTFILE ]; then rm -rf OUTPUTFILE; fi
CMD="hadd -f $OUTPUTFILE"
FILES=($(find $OUTPUTBASE -name $ROOTFILE))
for fl in ${FILES[@]}; do
    CMD=$(printf "%s %s" "$CMD" "$fl")
done

echo "Running: $CMD"
eval $CMD
echo "Done ..."