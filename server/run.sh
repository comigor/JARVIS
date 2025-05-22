#!/bin/bash
cd /app
export PYTHONPATH=$PWD/src

uv sync

uv run python -m jarvis.server
