#!/bin/bash

rm ../appengine.tar.gz
pushd build

find . -name "*.pyc" | xargs rm
tar -czf ../../appengine.tar.gz .

popd
