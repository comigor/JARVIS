#!/bin/bash
rm token.json

poetry install --no-root
export PYTHONPATH=$PWD/src
poetry run python -c 'from jarvis.tools.google.base import authenticate_with_google; authenticate_with_google()'

scp token.json brick:/DATA/AppData/homeassistant/custom_components/jarvis/server/token.json
