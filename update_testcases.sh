#!/bin/bash
mkdir -p testcases
cd testcases

if [ ! -d hhnk_gebiedsbreed ]
then
    echo "hhnk_gebiedsbreed subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/hhnk_gebiedsbreed
fi
cd hhnk_gebiedsbreed
hg pull -u
cd ..

if [ ! -d delfland_gebiedsbreed ]
then
    echo "delfland_gebiedsbreed subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/delfland_gebiedsbreed
fi
cd delfland_gebiedsbreed
hg pull -u
cd ..


if [ ! -d duifpolder_slice ]
then
    echo "duifpolder_slice subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/duifpolder_slice
fi
cd duifpolder_slice
hg pull -u
cd ..

if [ ! -d testcase ]
then
    echo "testcase subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/testcase
fi
cd testcase
hg pull -u
cd ..

if [ ! -d delfland-model-voor-3di ]
then
    echo "delfland-model-voor-3di subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/delfland-model-voor-3di
fi
cd delfland-model-voor-3di
hg pull -u
cd ..

if [ ! -d brouwersdam ]
then
    echo "brouwersdam subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/brouwersdam
fi
cd brouwersdam
hg pull -u
cd ..

if [ ! -d hhnkipad ]
then
    echo "hhnkipad subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/hhnkipad
fi
cd hhnkipad
hg pull -u
cd ..

if [ ! -d 1d-democase ]
then
    echo "1d-democase subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/1d-democase
fi
cd 1d-democase
hg pull -u
cd ..

if [ ! -d heerenveen ]
then
    echo "heerenveen subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/heerenveen
fi
cd heerenveen
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

if [ ! -d 1dpumptest ]
then
    echo "1dpumptest subdir doesn't exist, cloning it"
    hg clone http://hg-test.3di.lizard.net/1dpumptest
fi
cd 1dpumptest
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
