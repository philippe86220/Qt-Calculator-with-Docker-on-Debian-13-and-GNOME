#!/usr/bin/env bash
set -e

# Autorise temporairement les conteneurs locaux à accéder au serveur X11
xhost +local:docker

docker compose up -d --build


echo "calculatrice lancée. Pour l'arrêter : ./stop.sh"
