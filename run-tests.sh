#!/bin/sh
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

set -e

if [ ! -f "venv/bin/activate" ]; then
    echo "Setting up Python virtual environment."
    python3 -m venv "venv"
    . ./venv/bin/activate
    pip install -q -U pip setuptools wheel
    pip install -q -r dev-requirements.txt
    pip install -q -e .[oidc]
    # TODO Resolve this, temporary fix for https://github.com/scitt-community/scitt-api-emulator/issues/38
    pip install urllib3==1.26.15 requests-toolbelt==0.10.1
else
    . ./venv/bin/activate 
fi

pytest "$@"
