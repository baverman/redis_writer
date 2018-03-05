#!/bin/bash
set -e
pyver=${1:?Version is required}
shift
docker build --build-arg IMAGE=$pyver -t redis-writer-$pyver -f ci/Dockerfile.test ci
docker run --rm -w /build -u $UID:$GROUPS -v $PWD:/build redis-writer-$pyver ./ci/run-tests.sh "$@"
