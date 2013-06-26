#!/bin/sh
# Script that updates (and creates, if necessary) a bunch of
# testcases.
if [ ! -d testbank ]
then
    echo "testbank subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/testbank
fi
cd testbank;
hg pull -u
