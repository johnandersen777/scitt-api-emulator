#!/usr/bin/env bash

(
  while test 1; do
    for user in $(cat /var/run/alice-server/sshd.logs.txt | grep 'invalid user' | sed -e 's/.*invalid user //g' -e 's/ .*//g'); do
      found=$(grep -E "^${user}:" /etc/passwd);
      if [[ "x${found}" = "x" ]]; then
        useradd "${user}";
      fi;
    done;
    sleep 0.1;
  done
) &

mkdir -p /var/run/alice-server/
/usr/sbin/sshd -D -E /var/run/alice-server/sshd.logs.txt -f /etc/ssh/sshd_config
