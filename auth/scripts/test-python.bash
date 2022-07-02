#!/bin/bash

source venv/bin/activate
set -xe

pytest || exit
