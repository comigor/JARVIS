#!/bin/bash
cd /app
export PYTHONPATH=$PWD/src

pip install poetry
poetry install --no-root

poetry run python -m jarvis.server
