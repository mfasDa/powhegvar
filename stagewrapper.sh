#! /bin/bash

cmd=""
first=1
for x in ${@:1}; do
    if [ $first -eq 1 ]; then
        cmd=$x
        let "first=0"
    else
        cmd=$(printf "%s %s" "$cmd" "$x")
    fi
done
echo "Running: $cmd"
eval $cmd