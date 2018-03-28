#!/bin/bash
set -e
image=${1:?Docker image is required}
shift
pyver=$(basename $image)
docker build --build-arg IMAGE=$image -t redis-writer-$pyver -f ci/Dockerfile.test ci
docker run --rm -w /build -u $UID:$GROUPS -v $PWD:/build redis-writer-$pyver ./ci/run-tests.sh "$@"
