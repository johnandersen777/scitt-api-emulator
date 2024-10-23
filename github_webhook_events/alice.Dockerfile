FROM registry.fedoraproject.org/fedora

COPY ./entrypoint.sh /host/entrypoint.sh

RUN /host/entrypoint.sh

ENTRYPOINT /host/entrypoint.sh
