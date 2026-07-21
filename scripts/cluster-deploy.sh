#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ansible all -m ping
ansible-playbook playbooks/site.yml
ansible-playbook playbooks/status.yml
