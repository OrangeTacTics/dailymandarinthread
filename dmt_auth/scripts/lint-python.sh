#!/bin/bash

source venv/bin/activate
set -xe

mypy || exit
flake8 || exit
black --diff --check dmt_graphql || exit
python -m dmt_graphql.tools.schema_check --diff || exit
