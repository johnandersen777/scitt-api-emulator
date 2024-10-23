# docker build -t alice-server -f alice.Dockerfile . && docker run --rm -ti -p 2222:22 alice-server
FROM registry.fedoraproject.org/fedora as client

COPY ./entrypoint.sh /host/entrypoint.sh

RUN set -x \
  && export CALLER_PATH=/host \
  && /host/entrypoint.sh

ENTRYPOINT /host/entrypoint.sh

FROM client as server

RUN set -x \
  && dnf install -y openssh-server curl \
  && ssh-keygen -A

RUN set -x \
  && echo 'auth required pam_permit.so' | tee -a /etc/pam.d/sshd \
  && sed -i -e 's/^UsePAM no/UsePAM yes/g' /etc/ssh/sshd_config \
  && sed -i -e 's/^AuthorizedKeysFile/#AuthorizedKeysFile/g' /etc/ssh/sshd_config \
  && echo 'PermitUserEnvironment no' | tee -a /etc/ssh/sshd_config \
  && echo 'ForceCommand /bin/locked-shell.sh' | tee -a /etc/ssh/sshd_config \
  && echo 'PermitRootLogin no' | tee -a /etc/ssh/sshd_config \
  && echo 'PubkeyAuthentication yes' | tee -a /etc/ssh/sshd_config \
  && echo 'PasswordAuthentication no' | tee -a /etc/ssh/sshd_config \
  && echo 'AuthorizedKeysCommand /usr/bin/curl -sfL https://github.com/%u.keys' | tee -a /etc/ssh/sshd_config \
  && echo 'AuthorizedKeysCommandUser nobody' | tee -a /etc/ssh/sshd_config \
  && echo 'AuthorizedPrincipalsCommand /usr/bin/curl -sfL https://github.com/%u.keys' | tee -a /etc/ssh/sshd_config \
  && echo 'AuthorizedPrincipalsCommandUser nobody' | tee -a /etc/ssh/sshd_config

COPY locked-shell.sh /bin/
COPY entrypoint-server.sh /host/
COPY server_motd /host/

RUN set -x \
  && mkdir -pv /var/run/alice-server/ \
  && chmod +x /bin/locked-shell.sh

# TODO Remove bash, sh and other shells

ENTRYPOINT ["/host/entrypoint-server.sh"]
