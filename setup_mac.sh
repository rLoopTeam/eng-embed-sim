#!/bin/bash

# File:    setup_mac.sh
# Purpose: Set up anaconda and a virtualenv on a mac
# Author:  Ryan Adams
# Date:    2016-Dec-16

# @todo: rmdir anaconda and suppress error (will only work if it's empty)


# @todo: maybe add a -f to reinstall even if anaconda is already there? Maybe not...

ANACONDA_DOWNLOAD=https://repo.continuum.io/archive/Anaconda2-4.2.0-MacOSX-x86_64.sh
ANACONDA_FILENAME=Anaconda2-4.2.0-MacOSX-x86_64.sh

# Scrub path so you can run this from anywhere
SCRIPT_PATH="`dirname \"$0\"`"
SCRIPT_PATH="`( cd \"$SCRIPT_PATH\" && pwd )`"

# Utility for moving around in the directories
pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}


mkdir -p "$SCRIPT_PATH/downloads"


# Download Anaconda
if [ ! -f "$SCRIPT_PATH/downloads/$ANACONDA_FILENAME" ]; then
    pushd "$SCRIPT_PATH/downloads"
    wget $ANACONDA_DOWNLOAD
    popd
fi

# Install Anaconda locally
ANACONDA_PREFIX="$SCRIPT_PATH/anaconda"

# @todo: Check to see if anaconda is already installed and skip if so
echo "Installing Anaconda in $ANACONDA_PREFIX"
/bin/bash "$SCRIPT_PATH/downloads/$ANACONDA_FILENAME" -b -p "$ANACONDA_PREFIX"

# NOTE: RUN THESE COMMANDS MANUALLY
#alias conda="$SCRIPT_PATH/anaconda/bin/conda"
#conda update conda
#conda create -n venv python=2.7 anaconda

