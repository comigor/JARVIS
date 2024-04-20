from datetime import datetime
from fastapi import FastAPI
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langchain.agents import Tool
from langchain.prompts import MessagesPlaceholder
from langchain.tools.wikipedia.tool import WikipediaQueryRun
from langserve import add_routes
import logging
import os

from jarvis.tools.homeassistant.toolkit import HomeAssistantToolkit
from jarvis.tools.google.toolkit import GoogleToolkit

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes functions succinctly. You are observant of all the details in the data you have in order to come across as highly observant, emotionally intelligent and humanlike in your responses, always trying to use less than 30 words.

Answer the user's questions about the world truthfully. Be careful not to execute functions if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Always remember to use tools to make sure you're doing the best you can. So when you need to know what day or what time is it, for example, use a Python shell. When you want to retrieve up-to-date information about a topic, use Wikipedia. When you aren't sure about the existence of an entity, list all home entities, etc.

Right now is {datetime.now().astimezone().isoformat()}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Consider local holidays and treat them as non-work days.""",
        ),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="messages"),
        # ("user", "{input}"),
    ]
)


tools = [
    WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    Tool(
        name="python_repl",
        description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
        func=PythonREPL().run,
    ),
]
tools += HomeAssistantToolkit(
    base_url=os.environ["HOMEASSISTANT_URL"], api_key=os.environ["HOMEASSISTANT_KEY"]
).get_tools()
tools += GoogleToolkit().get_tools()


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=False)
llm_with_tools = llm.bind_tools(tools)

from jarvis.graph import generate_graph

graph = generate_graph(llm_with_tools, tools)

chain = (
    {
        "messages": prompt | RunnableLambda(lambda x: x.messages),
    }
    | graph
    | RunnableLambda(lambda x: x.get("agent").get("messages")[-1].content)
)

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    # input_messages_key="input",
    input_messages_key="messages",
    history_messages_key="history",
)


prompt2 = ChatPromptTemplate.from_messages(
    [
        ("user", "{input}"),
    ]
)

app = FastAPI()
add_routes(
    app,
    {
        "messages": prompt2 | RunnableLambda(lambda x: x.messages),
    }
    | with_message_history,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10055)
