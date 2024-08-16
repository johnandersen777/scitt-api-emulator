# CONTRIBUTING

## Development

Hot reload

```bash
nodemon -e rs,toml --exec 'clear; set -x; maturin develop && sleep 1 && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; echo $?; test 1'
```
