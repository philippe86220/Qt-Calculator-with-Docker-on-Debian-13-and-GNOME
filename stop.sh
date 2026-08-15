#!/usr/bin/env bash
set -e

docker compose down

# Révoque l'accès à X11 accordé par run.sh
xhost -local:docker
