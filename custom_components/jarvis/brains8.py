# import the library
from typing import Annotated
from kani import AIParam, Kani, ai_function, chat_in_terminal
from kani.engines.openai import OpenAIEngine
import os

# set up the engine as above
api_key = os.getenv("OPENAI_API_KEY")
api_base = 'http://127.0.0.1:8080/v1'
# model = 'thebloke__open-llama-7b-open-instruct-ggml__open-llama-7b-open-instruct.ggmlv3.q4_0.bin'
model = 'thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf'

# engine = OpenAIEngine(api_key, model="gpt-3.5-turbo-0613")
engine = OpenAIEngine(api_key, model=model, api_base=api_base)


# subclass Kani to add AI functions
class MyKani(Kani):
    # Adding the annotation to a method exposes it to the AI
    @ai_function()
    def get_weather(
        self,
        # and you can provide extra documentation about specific parameters
        location: Annotated[str, AIParam(desc="The city and state, e.g. San Francisco, CA")],
    ):
        """Get the current weather in a given location."""
        # In this example, we mock the return, but you could call a real weather API
        return f"Weather in {location}: Sunny, 72 degrees fahrenheit."


ai = MyKani(engine)
chat_in_terminal(ai)

# ➜ poetry run python custom_components/jarvis/brains8.py
# USER: hows the weather in sao paulo?
# DEBUG:kani:get_prompt() returned 522 tokens (505 always) in 1 messages (0 always)
# DEBUG:kani.messages:[1]>>> role=<ChatRole.USER: 'user'> content='hows the weather in sao paulo?' name=None function_call=None
# DEBUG:kani.engines.openai.client:POST https://api.openai.com/v1/chat/completions returned 200
# DEBUG:kani.engines.openai.client:{'id': 'chatcmpl-8T11F0oDM0tboefK1GmKxQbYL2FIE', 'object': 'chat.completion', 'created': 1701926121, 'model': 'gpt-3.5-turbo-0613', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': None, 'function_call': {'name': 'get_weather', 'arguments': '{\n"location": "Sao Paulo"\n}'}}, 'finish_reason': 'function_call'}], 'usage': {'prompt_tokens': 72, 'completion_tokens': 16, 'total_tokens': 88}, 'system_fingerprint': None}
# DEBUG:kani.messages:<<< role=<ChatRole.ASSISTANT: 'assistant'> content=None name=None function_call=FunctionCall(name='get_weather', arguments='{\n"location": "Sao Paulo"\n}')
# AI: Thinking (get_weather)...
# DEBUG:kani:Model requested call to get_weather with data: '{\n"location": "Sao Paulo"\n}'
# DEBUG:kani:get_weather responded with data: 'Weather in Sao Paulo: Sunny, 72 degrees fahrenheit.'
# DEBUG:kani:get_prompt() returned 565 tokens (505 always) in 3 messages (0 always)
# DEBUG:kani.messages:[3]>>> role=<ChatRole.FUNCTION: 'function'> content='Weather in Sao Paulo: Sunny, 72 degrees fahrenheit.' name='get_weather' function_call=None
# DEBUG:kani.engines.openai.client:POST https://api.openai.com/v1/chat/completions returned 200
# DEBUG:kani.engines.openai.client:{'id': 'chatcmpl-8T11GanyuDIDdZiwuwpFuDs1YfpRQ', 'object': 'chat.completion', 'created': 1701926122, 'model': 'gpt-3.5-turbo-0613', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'The weather in Sao Paulo is currently sunny with a temperature of 72 degrees Fahrenheit.'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 109, 'completion_tokens': 18, 'total_tokens': 127}, 'system_fingerprint': None}
# DEBUG:kani.messages:<<< role=<ChatRole.ASSISTANT: 'assistant'> content='The weather in Sao Paulo is currently sunny with a temperature of 72 degrees Fahrenheit.' name=None function_call=None
# AI: The weather in Sao Paulo is currently sunny with a temperature of 72 degrees Fahrenheit.