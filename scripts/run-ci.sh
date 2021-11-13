#!/bin/bash

pushd dmt_graphql
bash scripts/run-ci.sh
popd

pushd dmt_chairmanmao
bash scripts/run-ci.sh
popd
