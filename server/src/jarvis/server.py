from apscheduler.schedulers.background import BackgroundScheduler
from asyncio import Task
from datetime import datetime
from fastapi import FastAPI
from typing import Any
import asyncio
import logging
import os
import json


from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.messages.base import messages_to_dict
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_experimental.utilities import PythonREPL
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.agents import Tool

from langserve import add_routes

from jarvis.tools.homeassistant.toolkit import HomeAssistantToolkit
from jarvis.tools.google.toolkit import GoogleToolkit
from jarvis.tools.google.base import refresh_google_token
from jarvis.tools.matrix.toolkit import MatrixToolkit
from jarvis.tools.beancount import BeancountAddTransactionTool
from jarvis.tools.schedule_action import ScheduleActionTool
from jarvis.tools.long_term_facts_memory import (
    SaveLongTermFactsMemoryTool,
    LoadLongTermFactsMemoryTool,
)
from jarvis.graph.types import AgentState
from jarvis.graph.graph import generate_graph


_LOGGER = logging.getLogger(__name__)


logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def get_llm() -> BaseChatModel:
    if os.environ.get("GROQ_API_KEY"):
        return ChatGroq(
            model="llama3-70b-8192", temperature=0, streaming=False, timeout=30
        )
    else:
        return ChatOpenAI(model="gpt-4o", temperature=0, streaming=False, timeout=30)


llm = get_llm()

tools = [
    ScheduleActionTool(),
    BeancountAddTransactionTool(),
    # SaveLongTermFactsMemoryTool(llm=llm),
    # LoadLongTermFactsMemoryTool(llm=llm),
]
tools += HomeAssistantToolkit(
    base_url=os.environ["HOMEASSISTANT_URL"], api_key=os.environ["HOMEASSISTANT_KEY"]
).get_tools()
tools += GoogleToolkit().get_tools()
if os.environ.get("ENABLE_MATRIX"):
    tools += MatrixToolkit().get_tools()
tools += [
    Tool(
        name="wikipedia",
        description="A wrapper around Wikipedia. Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects. Input should be a search query.",
        func=WikipediaAPIWrapper().run,  # type: ignore
    ),
    Tool(
        name="python_repl",
        description="A Python shell. Use this to execute python commands. Input should be a valid python command. Always print the last line or the value you want with `print(...)`.",
        func=PythonREPL().run,
    ),
]

graph = generate_graph(llm, tools)

# from zep_cloud.langchain import ZepChatMessageHistory
# from zep_cloud.client import Zep
# def zep_session_history(session_id: str) -> ZepChatMessageHistory:
#     return ZepChatMessageHistory(
#         session_id=session_id,
#         zep_client=Zep(
#             api_key=os.environ["ZEP_API_KEY"],
#         ),
#         memory_type="perpetual",
#     )


def make_system_prompt_with_context() -> SystemMessage:
    return SystemMessage(
        content=f"""Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes functions succinctly. You are observant of all the details in the data you have in order to come across as highly observant, emotionally intelligent and humanlike in your responses, always trying to use less than 30 words in the language user has asked.

Answer the user's questions about the world truthfully. Be careful not to execute functions if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Always remember to use tools to make sure you're doing the best you can. So when you need to know what day or what time is it, for example, use a Python shell. For tools related to Home control, always list all entities first, to avoid using non-existent entities.

Use metric system and Celsius.

Right now is {datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Consider local holidays and treat them as non-work days.

Think and execute tools in English, but but always answer in brazilian portuguese."""
    )


def make_agent_state(v: dict[str, Any]) -> AgentState:
    v["messages"] += [HumanMessage(content=v["question"])]

    return AgentState(
        full_chat_history=[],
        compressed_context=[make_system_prompt_with_context()],
        messages=v["messages"],
    )


store: dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory(messages=[])
    return store[session_id]


# TODO: try to type this correctly so playground will work again
chain = RunnableWithMessageHistory(
    runnable=RunnableLambda(make_agent_state) | graph,  # type: ignore
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="messages",
)


def persist_chat_history(state: AgentState, config: RunnableConfig) -> str:
    session_id = config.get("configurable", {}).get("session_id", "fallback")
    # If I try to simply append messages to the history, they get duplicated
    store[session_id] = ChatMessageHistory(messages=list(state["messages"]))

    with open("chat_history.json", "w") as file:
        file.write(
            json.dumps(
                messages_to_dict(
                    list(
                        filter(
                            lambda m: isinstance(m, HumanMessage)
                            or (isinstance(m, AIMessage) and len(m.tool_calls) == 0),
                            [*state["full_chat_history"], *state["messages"]],
                        ),
                    )
                )
            )
        )
    return str(state["messages"][-1].content)


app = FastAPI()
add_routes(
    app,
    chain | RunnableLambda(persist_chat_history),
)


scheduler = BackgroundScheduler()


@scheduler.scheduled_job("interval", id="refresh_token", hours=1)
def refresh_token():
    _LOGGER.info("Refreshing Google user token...")
    refresh_google_token()


@scheduler.scheduled_job("interval", id="save_rooms", minutes=15)
async def save_rooms():
    from jarvis.tools.matrix.base import client

    if client:
        await client.command_save_client()


def start_matrix() -> Task:
    from jarvis.tools.matrix.base import main as matrix_main, client as matrix_client

    return asyncio.create_task(matrix_main(matrix_client))


def start_uvicorn() -> Task:
    scheduler.start()

    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=10055)
    server = uvicorn.Server(config)
    return asyncio.create_task(server.serve())


# https://stackoverflow.com/questions/76142431/how-to-run-another-application-within-the-same-running-event-loop
# https://jacobpadilla.com/articles/handling-asyncio-tasks
async def main():
    tasks = [
        *([start_matrix()] if os.environ.get("ENABLE_MATRIX") is not None else []),
        start_uvicorn(),
    ]

    _done, _pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)


if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=10055)
    asyncio.run(main())
