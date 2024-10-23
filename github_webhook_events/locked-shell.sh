#!/usr/bin/env bash
set -euo pipefail

if [ -n CALLER_PATH ]; then
  export CALLER_PATH="/host"
fi

cat "${CALLER_PATH}/server_motd"

trap bash EXIT

set +e

tmux -S "/tmp/${USER}.sock" list-sessions

bash

# TODO within python optionally after server connection established chmod 000 /tmp/$USER.sock
python -u "${CALLER_PATH}/agi.py" --socket-path "/tmp/${USER}.sock"
