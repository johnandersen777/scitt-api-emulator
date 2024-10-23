#!/usr/bin/env bash

if [[ "x${CALLER_PATH}" = "x" ]]; then
  export CALLER_PATH="/host"
fi
mkdir -p "${CALLER_PATH}"

(
  while test 1; do
    for user in $(cat /var/run/alice-server/sshd.logs.txt 2>/dev/null | grep 'invalid user' | sed -e 's/.*invalid user //g' -e 's/ .*//g'); do
      found=$(grep -E "^${user}:" /etc/passwd);
      if [[ "x${found}" = "x" ]]; then
        useradd "${user}" 1>/dev/null 2>&1;
      fi;
    done;
    sleep 0.1;
  done
) &

source "${CALLER_PATH}/util.sh"
# tail -F "${CALLER_PATH}/policy_engine.logs.txt" 2>/dev/null &
# NO_CELERY=1 python -u ${CALLER_PATH}/policy_engine.py api --bind 127.0.0.1:0 --workers 1 1>"${CALLER_PATH}/policy_engine.logs.txt" 2>&1 &
# export POLICY_ENGINE_PORT=$(grep 'Listening at' "${CALLER_PATH}/policy_engine.logs.txt" | sed -e 's/.*://g' -e 's/ .*//g')
# until [[ "x${POLICY_ENGINE_PORT}" != "x" ]]; do export POLICY_ENGINE_PORT=$(grep 'Listening at' "${CALLER_PATH}/policy_engine.logs.txt" | sed -e 's/.*://g' -e 's/ .*//g'); done
# echo "${POLICY_ENGINE_PORT}" > "${CALLER_PATH}/policy_engine_port.txt"

tail -F "${CALLER_PATH}/agi.logs.txt" 2>/dev/null &
(cd "${CALLER_PATH}" && python -m uvicorn "agi:app" --uds "${CALLER_PATH}/agi.sock" 1>"${CALLER_PATH}/agi.logs.txt" 2>&1 &)
# python -u ${CALLER_PATH}/agi.py --listen-unix "${CALLER_PATH}/agi.sock" 1>"${CALLER_PATH}/agi.logs.txt" 2>&1 &
# export POLICY_ENGINE_PORT=$(grep 'Listening at' "${CALLER_PATH}/policy_engine.logs.txt" | sed -e 's/.*://g' -e 's/ .*//g')
# until [[ "x${POLICY_ENGINE_PORT}" != "x" ]]; do export POLICY_ENGINE_PORT=$(grep 'Listening at' "${CALLER_PATH}/policy_engine.logs.txt" | sed -e 's/.*://g' -e 's/ .*//g'); done
# echo "${POLICY_ENGINE_PORT}" > "${CALLER_PATH}/policy_engine_port.txt"

mkdir -p /var/run/alice-server/
/usr/sbin/sshd -D -E /var/run/alice-server/sshd.logs.txt -f /etc/ssh/sshd_config
