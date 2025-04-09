# docker build --progress=plain -t alice-server -f agi_sshd.Dockerfile . && docker run --rm -ti -p 2222:2222 -e OPENAI_API_KEY=$(python -m keyring get $(git config user.email) api-key.platform.openai.com) alice-server
FROM golang:1.24 as builder_golang_agi_sshd

WORKDIR /usr/src/app

# pre-copy/cache go.mod for pre-downloading dependencies and only redownloading them in subsequent builds if they change
COPY go.mod go.sum ./
RUN go mod download

COPY agi_sshd.go .

RUN set -x \
  && CGO_ENABLED=0 go build -tags netgo -o agi_sshd agi_sshd.go

# Python server, add built golang server
FROM registry.fedoraproject.org/fedora as client

COPY ./entrypoint.sh /host/entrypoint.sh

RUN set -x \
  && export CALLER_PATH=/host \
  && /host/entrypoint.sh

ENTRYPOINT /host/entrypoint.sh

FROM client as server

RUN set -x \
  && dnf install -y curl tmux socat

# TODO Caching
# RUN bash -xec "$(grep 'pip install' /host/agi.py | head -n 1)"
RUN set -x \
  && python -m pip install -U pip setuptools wheel snoop openai openai-agents keyring keyrings-alt libtmux psutil \
  && python -m pip install --force-reinstall \
       'mcp@git+https://github.com/johnandersen777/python-sdk@mcp_enable_over_unix_socket' \
       'openai-agents@git+https://github.com/johnandersen777/openai-agents-python@additional_properties_dict_keys_mcp_enable_over_unix_socket'

COPY server_motd /host/
COPY openai_assistant_instructions.md /host/
COPY agi.py /host/
COPY util.sh /host/
COPY entrypoint-server.sh /host/
COPY entrypoint.sh /host/
COPY mcp_server_files.py /host/
COPY Caddyfile /host/

RUN set -x \
  && export CALLER_PATH=/host \
  && bash -xe /host/entrypoint.sh

RUN set -x \
  && mkdir -pv /var/run/alice-server/

COPY --from=builder_golang_agi_sshd /usr/src/app/agi_sshd /usr/bin/agi_sshd

# TODO Remove bash, sh and other shells

ENTRYPOINT ["/host/entrypoint-server.sh"]
