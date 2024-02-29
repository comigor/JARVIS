#!/usr/bin/env python
"""Example LangChain server exposes and agent that has conversation history.

In this example, the history is stored entirely on the client's side.

Please see other examples in LangServe on how to use RunnableWithHistory to
store history on the server side.

Relevant LangChain documentation:

* Creating a custom agent: https://python.langchain.com/docs/modules/agents/how_to/custom_agent
* Streaming with agents: https://python.langchain.com/docs/modules/agents/how_to/streaming#custom-streaming-with-events
* General streaming documentation: https://python.langchain.com/docs/expression_language/streaming
* Message History: https://python.langchain.com/docs/expression_language/how_to/message_history

**ATTENTION**
1. To support streaming individual tokens you will need to use the astream events
   endpoint rather than the streaming endpoint.
2. This example does not truncate message history, so it will crash if you
   send too many messages (exceed token length).
3. The playground at the moment does not render agent output well! If you want to
   use the playground you need to customize it's output server side using astream
   events by wrapping it within another runnable.
4. See the client notebook it has an example of how to use stream_events client side!
"""  # noqa: E501
import os
from typing import Any, List, Union

from datetime import datetime
from fastapi import FastAPI
from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.prompts import MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.messages import AIMessage, FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool

from langserve import add_routes
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.toolkit import HomeAssistantToolkit
from jarvis.tools.google.toolkit import GoogleToolkit

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f'''Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes functions succinctly. You are observant of all the details in the data you have in order to come across as highly observant, emotionally intelligent and humanlike in your responses, always trying to use less than 30 words.

Answer the user's questions about the world truthfully. Be careful not to execute functions if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Always remember to use tools to make sure you're doing the best you can. So when you need to know what day or what time is it, for example, use a Python shell. When you want to retrieve up-to-date information about a topic, use Wikipedia. When you aren't sure about the existence of an entity, list all home entities, etc.

Right now is {datetime.now().astimezone().isoformat()}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Consider local holidays and treat them as non-work days.''',
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


@tool
def word_length(word: str) -> int:
    """Returns a counter word"""
    return len(word)


# We need to set streaming=True on the LLM to support streaming individual tokens.
# Tokens will be available when using the stream_log / stream events endpoints,
# but not when using the stream endpoint since the stream implementation for agent
# streams action observation pairs not individual tokens.
# See the client notebook that shows how to use the stream events endpoint.
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.25, streaming=True)

tools = [
    word_length,
    WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    Tool(
        name="python_repl",
        description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
        func=PythonREPL().run,
    ),
]
tools += HomeAssistantToolkit(base_url = os.environ['HOMEASSISTANT_URL'], api_key = os.environ['HOMEASSISTANT_KEY']).get_tools()
tools += GoogleToolkit().get_tools()


llm_with_tools = llm.bind(tools=[convert_to_openai_tool(tool) for tool in tools])

# ATTENTION: For production use case, it's a good idea to trim the prompt to avoid
#            exceeding the context window length used by the model.
#
# To fix that simply adjust the chain to trim the prompt in whatever way
# is appropriate for your use case.
# For example, you may want to keep the system message and the last 10 messages.
# Or you may want to trim based on the number of tokens.
# Or you may want to also summarize the messages to keep information about things
# that were learned about the user.
#
# def prompt_trimmer(messages: List[Union[HumanMessage, AIMessage, FunctionMessage]]):
#     '''Trims the prompt to a reasonable length.'''
#     # Keep in mind that when trimming you may want to keep the system message!
#     return messages[-10:] # Keep last 10 messages.

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    # | prompt_trimmer # See comment above.
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using LangChain's Runnable interfaces",
)


# We need to add these input/output schemas because the current AgentExecutor
# is lacking in schemas.
class Input(BaseModel):
    input: str
    # The field extra defines a chat widget.
    # Please see documentation about widgets in the main README.
    # The widget is used in the playground.
    # Keep in mind that playground support for agents is not great at the moment.
    # To get a better experience, you'll need to customize the streaming output
    # for now.
    chat_history: List[Union[HumanMessage, AIMessage, FunctionMessage]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "input", "output": "output"}},
    )


class Output(BaseModel):
    output: Any


# Adds routes to the app for using the chain under:
# /invoke
# /batch
# /stream
# /stream_events
add_routes(
    app,
    agent_executor.with_types(input_type=Input, output_type=Output).with_config(
        {"run_name": "agent"}
    ),
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10055)
