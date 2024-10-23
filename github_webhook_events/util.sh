node_install() {
  sudo dnf install -y node
}

deno_install() {
  if [ ! -f /usr/bin/deno ]; then
    curl -fsSL https://deno.land/install.sh | sh
    export DENO_INSTALL="${HOME}/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
    hash -r
    cp -v $(which deno) /usr/bin/deno || true
  fi
}

submit_policy_engine_request() {
    tail -F "${CALLER_PATH}/policy_engine.logs.txt" &
    TAIL_PID=$!

    TASK_ID=$(curl -X POST -H "Content-Type: application/json" -d @<(cat "${CALLER_PATH}/request.yml" | python -c 'import json, yaml, sys; print(json.dumps(yaml.safe_load(sys.stdin.read()), indent=4, sort_keys=True))') http://localhost:8080/request/create  | jq -r .detail.id)

    STATUS=$(curl -sfL http://localhost:8080/request/status/$TASK_ID | jq -r .status)
    while [ "x${STATUS}" != "xcomplete" ]; do
        STATUS=$(curl -sfL http://localhost:8080/request/status/$TASK_ID | jq -r .status)
    done
    kill "${TAIL_PID}"
    STATUS=$(curl -sfL http://localhost:8080/request/status/$TASK_ID | python -m json.tool > "${CALLER_PATH}/last-request-status.json")
    cat "${CALLER_PATH}/last-request-status.json" | jq
    export STATUS=$(cat "${CALLER_PATH}/last-request-status.json" | jq -r .status)
}

policy_engine_deps() {
  python -m pip install -U pip setuptools wheel build
  python -m pip install -U pyyaml snoop pytest httpx cachetools aiohttp gidgethub[aiohttp] celery[redis] fastapi pydantic gunicorn uvicorn
}
