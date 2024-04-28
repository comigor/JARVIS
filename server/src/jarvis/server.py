from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from fastapi import FastAPI
import logging
import os
from typing import Any

from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langchain.agents import Tool
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from langserve import add_routes

from jarvis.tools.homeassistant.toolkit import HomeAssistantToolkit
from jarvis.tools.google.toolkit import GoogleToolkit
from jarvis.tools.google.base import refresh_google_token
from jarvis.graph import generate_graph


_LOGGER = logging.getLogger(__name__)


logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def make_system_message():
    return f"""Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes functions succinctly. You are observant of all the details in the data you have in order to come across as highly observant, emotionally intelligent and humanlike in your responses, always trying to use less than 30 words in the language user has asked.

Answer the user's questions about the world truthfully. Be careful not to execute functions if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Always remember to use tools to make sure you're doing the best you can. So when you need to know what day or what time is it, for example, use a Python shell. For tools related to Home control, always list all entities first, to avoid using non-existent entities.

Use metric system and Celsius.

Right now is {datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Consider local holidays and treat them as non-work days."""


tools = [
    Tool(
        name="wikipedia",
        description="A wrapper around Wikipedia. Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects. Input should be a search query.",
        func=WikipediaAPIWrapper().run,  # type: ignore
    ),
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


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=False, timeout=30)
llm_with_tools = llm.bind_tools(tools)


graph = generate_graph(llm_with_tools, tools)


def adapt_messages_dict(input: str) -> dict[str, Any]:
    return {"messages": [HumanMessage(content=input)]}


def get_agent_response(chain_result: dict[str, Any]) -> str:
    return str(chain_result.get("agent", chain_result).get("messages")[-1].content)


store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory(
            messages=[SystemMessage(content=make_system_message())],
        )
    return store[session_id]


chain = graph | RunnableLambda(get_agent_response)

with_message_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="messages",
    history_messages_key="history",
    output_messages_key="output",
)

app = FastAPI()
add_routes(
    app,
    RunnableLambda(adapt_messages_dict) | with_message_history,
)


scheduler = BackgroundScheduler()


@scheduler.scheduled_job("interval", id="refresh_token", hours=1)
def refresh_token():
    _LOGGER.info("Refreshing Google user token...")
    refresh_google_token()


if __name__ == "__main__":
    scheduler.start()

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10055)
