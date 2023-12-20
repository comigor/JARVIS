import logging
import os
import openai
import itertools


from actionweaver.llms.openai.chat import OpenAIChatCompletion
from actionweaver.llms.openai.tokens import TokenUsageTracker
from actionweaver import action

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = 'http://127.0.0.1:8080/v1'
# model = 'thebloke__airoboros-m-7b-3.1.2-gguf__airoboros-m-7b-3.1.2.q5_k_m.gguf'
model = 'thebloke__open-llama-7b-open-instruct-ggml__open-llama-7b-open-instruct.ggmlv3.q4_0.bin'

logging.basicConfig(
    filename='agent.log',
    filemode='a',
    format='%(asctime)s.%(msecs)04d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@action(name="GetCurrentTime")
def get_current_time() -> str:
    """
    Use this for getting the current time in the specified time zone.
    
    :return: A string representing the current time in the specified time zone.
    """
    import datetime
    current_time = datetime.datetime.now()
    
    return f"The current time is {current_time}"


@action(name="Sleep")
def sleep(seconds: int) -> str:
    """
    Introduces a sleep delay of the specified seconds and returns a message.

    Args:
        seconds (int): The duration to sleep in seconds.

    Returns:
        str: A message indicating the completion of the sleep.
    """
    import time
    time.sleep(seconds)
    return f"Now I wake up after sleep {seconds} seconds."

chat = OpenAIChatCompletion(model, token_usage_tracker = TokenUsageTracker(budget=2000, logger=logger), logger=logger)

def print_output(output):
    if type(output) == itertools._tee:
        for chunk in output:
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content is not None:
                print(content, end='')
    else:
        print (output)

aaa = chat.create([{"role": "user", "content": "hello"}], actions = [sleep, get_current_time])

# print_output(aaa)
print(aaa)