#!/bin/bash

set -xe

REGISTRY=${1:-"localhost"}

podman build \
    -t $REGISTRY/dmt-chairmanmao:latest \
    -f dmt_chairmanmao/Dockerfile

podman build \
    -t $REGISTRY/dmt-graphql:latest \
    -f dmt_graphql/Dockerfile

podman build \
    -t $REGISTRY/dmt-auth:latest \
    -f dmt_auth/Dockerfile

podman build \
    -t $REGISTRY/dmt-dailymandarinthreadinfo:latest \
    -f dmt_dailymandarinthreadinfo/Dockerfile
