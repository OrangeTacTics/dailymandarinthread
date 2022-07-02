#!/bin/bash

bash scripts/install-python.sh
bash scripts/lint-python.sh
# bash scripts/test-python.sh
rm -rf venv
