FROM mcr.microsoft.com/devcontainers/base:ubuntu-20.04@sha256:18acf0769f2ea2a610ab724c4a11108fdb595a4b46cb0c2c5ce6f28d497e0371

COPY requirements.txt /tmp/pip-tmp/requirements.txt

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-pip \
    && pip3 install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
