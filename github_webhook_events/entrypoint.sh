#!/usr/bin/env bash
set -xeuo pipefail

export EDITOR=vim

# TODO Per distro dependencies via /usr/lib/os-release and
# /etc/os-release bash source | env
if [ ! -f /usr/bin/node ]; then
  dnf install -y git vim openssh jq python python-pip unzip nodejs
fi

if [ ! -f /usr/bin/deno ]; then
  curl -fsSL https://deno.land/install.sh | sh
  export DENO_INSTALL="${HOME}/.deno"
  export PATH="$DENO_INSTALL/bin:$PATH"
  hash -r
  cp -v $(which deno) /usr/bin/deno || true
fi

policy_engine_deps() {
  python -m pip install -U pip setuptools wheel build
  python -m pip install -U pyyaml snoop pytest httpx cachetools aiohttp gidgethub[aiohttp] celery[redis] fastapi pydantic gunicorn uvicorn
}

if [ ! -f "${CALLER_PATH}/policy_engine.py" ]; then
  policy_engine_deps

  curl -sfLO https://github.com/pdxjohnny/scitt-api-emulator/raw/policy_engine_cwt_rebase/scitt_emulator/policy_engine.py
fi
