#!/bin/bash

virtualenv -p "python3.8" venv
source venv/bin/activate
pip install .
pip install mypy flake8 black pytest
