import enum
import os
import openai
from openai_functions import Conversation

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = 'http://127.0.0.1:8080/v1'
model = 'thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf'

conversation = Conversation(model=model)

class Unit(enum.Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"

@conversation.add_function()
def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> dict:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return {
        "location": location,
        "temperature": "72",
        "unit": unit.value,
        "forecast": ["sunny", "windy"],
    }

response = conversation.ask("What's the weather in celsius in San Francisco?")

print(response)
