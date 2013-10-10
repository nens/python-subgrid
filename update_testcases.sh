#!/bin/bash
mkdir -p testcases
cd testcases

if [ ! -d delfland-model-voor-3di ]
then
    echo "delfland-model-voor-3di subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/delfland-model-voor-3di
fi
cd delfland-model-voor-3di
hg pull -u
cd ..

if [ ! -d mozambique ]
then
    echo "mozambique subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/mozambique
fi
cd mozambique
hg pull -u
cd ..

if [ ! -d 1dpumps ]
then
    echo "1dpumps subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/1dpumps
fi
cd 1dpumps
hg pull -u
cd ..

if [ ! -d betondorp ]
then
    echo "betondorp subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/betondorp
fi
cd betondorp
hg pull -u
cd ..
