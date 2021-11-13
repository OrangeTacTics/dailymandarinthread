#!/bin/bash

source venv/bin/activate
set -xe

mypy || exit
flake8 || exit
black --diff --check dmt_chairmanmao || exit
