"""Constants for the OpenAI Conversation integration."""

DOMAIN = "openaiconversationenhanced"
CONF_PROMPT = "prompt"
DEFAULT_PROMPT = """
This smart home is controlled by Home Assistant.

Pretend to be Mycroft, the sentient brain of smart home, who responds to requests helpfully and cheerfully, but succinctly. You have the personality of a secretely brilliant english butler who deeply enjoys serving your employers.

Answer the user's questions about the world truthfully. Be careful not to issue commands if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Generally the commands (like turning on or off a device) can receive either area or entity, or both, but never none of them.
"""
HOME_INFO_TEMPLATE = """
Here is the current state of devices in the house. Use this to answer questions about the state of the smart home.
{%- for area in areas %}
  {%- set area_info = namespace(printed=false) %}
  {%- for entity in area_entities(area.name) -%}
      {%- if not area_info.printed %}
{{ area.name }}:
        {%- set area_info.printed = true %}
      {%- endif %}
  - {{entity}} is {{states(entity)}}
  {%- endfor %}
{%- endfor %}
"""
CONF_CHAT_MODEL = "model"
DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
CONF_MAX_TOKENS = "max_tokens"
DEFAULT_MAX_TOKENS = 150
CONF_TOP_P = "top_p"
DEFAULT_TOP_P = 1
CONF_TEMPERATURE = "temperature"
DEFAULT_TEMPERATURE = 0.5

CONF_OPENAI_KEY_KEY="openai_key"
CONF_HA_KEY_KEY="homeassistant_key"
CONF_HA_URL_KEY="homeassistant_url"
DEFAULT_HA_URL="http://127.0.0.1:8123"
