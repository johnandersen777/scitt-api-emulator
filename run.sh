#!/usr/bin/env bash
set -xeuo pipefail

rm -rf .venv && \
python -m venv .venv && \
. .venv/bin/activate && \
pip install -U pip setuptools wheel && \
pip install \
  toml \
  bovine{-store,-process,-pubsub,-herd,-tool} \
  'https://codeberg.org/pdxjohnny/bovine/archive/activitystreams_collection_helper_enable_multiple_iterations.tar.gz#egg=bovine&subdirectory=bovine' \
  'https://codeberg.org/pdxjohnny/mechanical_bull/archive/event_loop_on_connect_call_handlers.tar.gz#egg=mechanical-bull'

export HYPERCORN_PID=0
function kill_hypercorn() {
  kill "${HYPERCORN_PID}"
}
hypercorn app:app &
export HYPERCORN_PID=$!
trap kill_hypercorn EXIT
sleep 1

export HANDLE_NAME=alice
export BOVINE_NAME=$(python -m bovine_tool.register "${HANDLE_NAME}" --domain http://localhost:8000 | awk '{print $NF}')
python -m mechanical_bull.add_user --accept "${HANDLE_NAME}" http://localhost:8000
python -m bovine_tool.manage "${BOVINE_NAME}" --did_key key0 $(cat config.toml | python -c 'import sys, tomllib, bovine.crypto; print(bovine.crypto.private_key_to_did_key(tomllib.load(sys.stdin.buffer)[sys.argv[-1]]["secret"]))' "${HANDLE_NAME}")

python -c 'import sys, pathlib, toml; path = pathlib.Path(sys.argv[-3]); obj = toml.loads(path.read_text()); obj[sys.argv[-2]]["handlers"][sys.argv[-1]] = True; path.write_text(toml.dumps(obj))' config.toml "${HANDLE_NAME}" scitt_handler

PYTHONPATH=${PYTHONPATH:-''}:$PWD timeout 5s python -m mechanical_bull.run
