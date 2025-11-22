#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
    set -- up
fi

docker compose -f docker-compose.yaml "$@"
