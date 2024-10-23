# Upstream: https://princeton-nlp.github.io/SWE-agent/installation/docker/
OPENAI_MODEL_SLUG="gpt4"

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock \
  -v "${CWD}/keys.cfg:/app/keys.cfg" \
  sweagent/swe-agent-run:latest \
  python run.py --image_name=sweagent/swe-agent:latest \
  --model_name "${OPENAI_MODEL_SLUG}"\
  --data_path "${GITHUB_ISSUE_URL}" \
  --config_file config/default_from_url.yaml \
  --skip_existing=False

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock \
  -e GITHUB_TOKEN="$(gh auth token)" \
  -e OPENAI_API_KEY="$(python -m keyring get ${USER} )" \
  sweagent/swe-agent-run:latest \
  # rest of the command above
