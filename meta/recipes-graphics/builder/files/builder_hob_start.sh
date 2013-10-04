#!/bin/sh
#This script will be called via mini X session on behalf of file owner, after
#installed in /etc/mini_x/session.d/. Any auto start jobs including X apps can
#be put here

# start hob here
export PSEUDO_PREFIX=/usr
export PSEUDO_LOCALSTATEDIR=/home/builder/pseudo
export PSEUDO_LIBDIR=/usr/lib/pseudo/lib64
<<<<<<< HEAD
export GIT_PROXY_COMMAND=/home/builder/poky/scripts/oe-git-proxy

#start pcmanfm in daemon mode to allow asynchronous launch
pcmanfm -d&

#register handlers for some file types
if [ ! -d /home/builder/.local/share/applications ]; then
    mkdir -p /home/builder/.local/share/applications/
    #register folders to open with PCManFM filemanager
    xdg-mime default pcmanfm.desktop inode/directory

    #register html links and files with Midori
    xdg-mime default midori.desktop x-scheme-handler/http
    xdg-mime default midori.desktop x-scheme-handler/https
    xdg-mime default midori.desktop text/html
fi
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

cd /home/builder/poky
. ./oe-init-build-env

#uncomment the settings for BB_NUMBER_THREADS and PARALLEL_MAKE
sed -i 's/^#BB_NUMBER_THREADS =/BB_NUMBER_THREADS =/g' conf/local.conf
sed -i 's/^#PARALLEL_MAKE =/PARALLEL_MAKE =/g' conf/local.conf

hob &

matchbox-terminal&

/etc/mini_x/please_wait_dialog.py &
