#!/usr/bin/env bash
set -euo pipefail
apt-get update
apt-get install -y ansible openssh-client git rsync
ansible --version
