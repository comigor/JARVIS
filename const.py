"""Constants for the OpenAI Conversation integration."""

DOMAIN="jarvis"
CONF_OPENAI_KEY_KEY="openai_key"
CONF_HA_KEY_KEY="homeassistant_key"
CONF_HA_URL_KEY="homeassistant_url"
CONF_GOOGLE_API_KEY="google_api_key"
CONF_GOOGLE_CX_KEY="google_cx_key"

import os
from pathlib import Path
ROOT_DIR = Path(os.path.dirname(os.path.abspath(globals().get('__file__', 'const.py'))))
