#!/usr/bin/env bash
set -euo pipefail

if [ -n CALLER_PATH ]; then
  export CALLER_PATH="/host"
fi

cat "${CALLER_PATH}/server_motd"

curl -sfL --unix-socket /host/agi.sock "http://localhost/connect/${USER}" | jq

# TODO within python optionally after server connection established chmod 000 /tmp/$USER.sock
# exec python -u "${CALLER_PATH}/agi.py" --socket-path "/tmp/${USER}.sock" --openai-api-key "${OPENAI_API_KEY}"
exec tail -F /dev/null
