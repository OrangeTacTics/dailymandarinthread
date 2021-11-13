#!/bin/bash

podman build \
    -t dmt-chairmanmao:latest \
    -f dmt_chairmanmao/Dockerfile

podman build \
    -t dmt-graphql:latest \
    -f dmt_graphql/Dockerfile
