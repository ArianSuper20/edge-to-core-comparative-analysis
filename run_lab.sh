#!/usr/bin/env bash
# Run the test lab container. Execute from repo root.
set -e
cd "$(dirname "$0")"
docker compose build lab
docker compose run --rm lab
