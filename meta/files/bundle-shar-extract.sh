#!/bin/bash

verbose=0
listcontents=0
prepare_buildsystem="yes"
while getopts "Dln" OPT; do
        case $OPT in
        D)
                verbose=1
                ;;
        l)
                listcontents=1
                ;;
        n)
                prepare_buildsystem="no"
                ;;
        *)
                echo "Usage: $(basename "$0") [-D] [-l] [-n]"
                echo "  -D         Use set -x to see what is going on"
                echo "  -l         list files that will be extracted"
                echo "  -n         Extract files but do not prepare the build system"
                exit 1
                ;;
        esac
done

if [ $verbose = 1 ] ; then
        set -x
fi

payload_offset=$(($(grep -na -m1 "^MARKER:$" "$0"|cut -d':' -f1) + 1))

if [ "$listcontents" = "1" ] ; then
    tail -n +$payload_offset "$0"| tar tv || exit 1
    exit
fi


tail -n +$payload_offset "$0"| tar mx --zstd --checkpoint=.2500 || exit 1

if [ $prepare_buildsystem = "no" ] ; then
        exit
fi

target_dir=$(basename "$0" .sh)
pushd $target_dir
layers/setup-build setup -c build-config-default -b build --no-shell > setup-build.log
popd

echo "Each time you wish to use this build in a new shell session, you need to source the environment setup script:"
echo " \$ . $target_dir/build/init-build-env"

exit 0

MARKER:
