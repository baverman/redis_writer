#!/bin/sh
redis-server &
exec py.test "$@"
