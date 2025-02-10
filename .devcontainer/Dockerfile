FROM mcr.microsoft.com/devcontainers/base:ubuntu-20.04@sha256:fb999144dd20bde5de9e06d8a5425d5611e17353ae37c5800adcc27d6c4e5bf2

COPY requirements.txt /tmp/pip-tmp/requirements.txt

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-pip \
    && pip3 install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
