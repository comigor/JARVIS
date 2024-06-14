from asyncio import Task
from fastapi import FastAPI
import asyncio
import logging
import os


from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.language_models.chat_models import BaseChatModel
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
from jarvis.graph.graph import generate_graph
from jarvis.tools.overseer.toolkit import OverseerToolkit


_LOGGER = logging.getLogger(__name__)


logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

DEBUG = os.environ.get("DEBUG")


def get_llm() -> BaseChatModel:
    if DEBUG:
        return ChatOpenAI(model="gpt-4o", temperature=0, streaming=False, timeout=30)

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
tools += OverseerToolkit(
    base_url=os.environ["OVERSEER_URL"], api_key=os.environ["OVERSEER_API_KEY"]
).get_tools()

graph = generate_graph(llm, tools)

app = FastAPI()
add_routes(app, graph)

if not DEBUG:
    from apscheduler.schedulers.background import BackgroundScheduler

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

    scheduler.start()


def start_matrix() -> Task:
    from jarvis.tools.matrix.base import main as matrix_main, client as matrix_client

    return asyncio.create_task(matrix_main(matrix_client))


def start_uvicorn() -> Task:
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=10055)
    server = uvicorn.Server(config)
    return asyncio.create_task(server.serve())


# https://stackoverflow.com/questions/76142431/how-to-run-another-application-within-the-same-running-event-loop
# https://jacobpadilla.com/articles/handling-asyncio-tasks
async def main():
    tasks = [
        *([start_matrix()] if not DEBUG else []),
        start_uvicorn(),
    ]

    _done, _pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)


if __name__ == "__main__":
    asyncio.run(main())
