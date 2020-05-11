#!/bin/bash

rm ../appengine.tar.gz
pushd src

find . -name "*.pyc" | xargs rm
tar -czf ../../appengine.tar.gz .

popd
