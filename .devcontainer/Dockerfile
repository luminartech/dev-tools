FROM mcr.microsoft.com/devcontainers/base:ubuntu-20.04@sha256:8d29fff9fb395dfe5f7838ef54f487eef47e1da2426e62503d01fdb6d3430b15

COPY requirements.txt /tmp/pip-tmp/requirements.txt

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-pip \
    && pip3 install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
