#!/bin/bash
mkdir -p testcases
cd testcases

if [ ! -d hhnk_gebiedsbreed ]
then
    echo "hhnk_gebiedsbreed subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/hhnk_gebiedsbreed
fi
pushd hhnk_gebiedsbreed
hg pull -u
popd

if [ ! -d delfland-gebiedsbreed ]
then
    echo "delfland-gebiedsbreed subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/delfland-gebiedsbreed
fi
pushd delfland-gebiedsbreed
hg pull -u
popd

if [ ! -d duifp ]
then
    echo "duifp subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/duifp
fi
pushd duifp
hg pull -u
popd

if [ ! -d hhnkipad ]
then
    echo "hhnkipad subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/hhnkipad
fi
pushd hhnkipad
hg pull -u
popd

if [ ! -d 1dpumptest ]
then
    echo "1dpumptest subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/1dpumptest
fi
pushd 1dpumptest
hg pull -u
popd

if [ ! -d 1d-democase ]
then
    echo "1d-democase subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/1d-democase
fi
pushd 1d-democase
hg pull -u
popd


if [ ! -d betondorp ]
then
    echo "betondorp subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/betondorp
fi
pushd betondorp
hg pull -u
popd

if [ ! -d testcase ]
then
    echo "testcase subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/testcase
fi
pushd testcase
hg pull -u
popd

