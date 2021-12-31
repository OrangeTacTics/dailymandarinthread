#!/bin/bash

set -xe

REGISTRY=${1:-"localhost"}
DOCKER_BIN=${DOCKER_BIN:-"docker"}
TAG=${TAG:-"local"}

$DOCKER_BIN build \
    -t $REGISTRY/dmt-chairmanmao:$TAG \
    -f dmt_chairmanmao/Dockerfile \
    dmt_chairmanmao

$DOCKER_BIN build \
    -t $REGISTRY/dmt-graphql:$TAG \
    -f dmt_graphql/Dockerfile \
    dmt_graphql

$DOCKER_BIN build \
    -t $REGISTRY/dmt-auth:$TAG \
    -f dmt_auth/Dockerfile \
    dmt_auth

$DOCKER_BIN build \
    -t $REGISTRY/dmt-dailymandarinthreadinfo:$TAG \
    -f dmt_dailymandarinthreadinfo/Dockerfile \
    dmt_dailymandarinthreadinfo

$DOCKER_BIN build \
    -t $REGISTRY/dmt-profiles:$TAG \
    -f dmt_profiles/Dockerfile \
    dmt_profiles
