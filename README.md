```bash
history -w /dev/stdout | grep nodemon | sort | uniq | grep maturin | tee -a README.md
nodemon -e rs,toml --exec 'clear; maturin develop 2>&1 | head -n 50; test 1'
nodemon -e rs,toml --exec 'clear; maturin develop && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; test 1'
nodemon -e rs,toml --exec 'clear; maturin develop; test 1'
nodemon -e rs,toml --exec 'clear; maturin develop; test 1' cat request.json | python -uc 'import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())'
nodemon -e rs,toml --exec 'clear; set -x; maturin develop && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; test 1'
nodemon -e rs,toml --exec 'clear; set -x; maturin develop && sleep 1 && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; echo $?; test 1'
nodemon -e rs,toml --exec 'clear; set -x; maturin develop && sleep 1 && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; test 1'
nodemon -e rs,toml --exec 'clear; set -x; python -m maturin develop && sleep 1 && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; echo $?; test 1'
nodemon -e rs,toml --exec 'clear; set -x; python --version && maturin develop && sleep 1 && cat request.json | python -uc "import sys; from scitt_api_emulator_rust_policy_engine import *; parse_policy_engine_request(sys.stdin.read())"; echo $?; test 1'
```
