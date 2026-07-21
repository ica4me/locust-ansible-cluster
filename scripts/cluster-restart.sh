#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ansible-playbook playbooks/restart.yml
ansible-playbook playbooks/status.yml
