import os
import asyncio

from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import MessagesPlaceholder, SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain.memory.chat_message_histories import FileChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate

from abilities.stocks import CurrentStockPriceTool, StockPerformanceTool
from abilities.homeassistant import HomeAssistantAbility
from abilities.python_repl import PythonREPLTool
from abilities.google.google_calendar import GoogleCalendarAbility
from abilities.google.google_search import GoogleSearchAbility
from abilities.google.google_tasks import GoogleTasksAbility
from abilities.tmdb import MovieSearchAbility
from abilities.wikipedia import WikipediaAbility
from abilities.matrix.send_message import MatrixSendMessageAbility

from abilities.base import BaseAbility

async def get_ai(abilities: [BaseAbility]) -> AgentExecutor:
    llm = ChatOpenAI(model='gpt-3.5-turbo-1106', temperature=0.2)

    chat_history_examples = []
    system_prompt = ''
    all_tools = [
        PythonREPLTool,
        CurrentStockPriceTool(),
        StockPerformanceTool(),
    ]

    ability: BaseAbility # only for typings
    for ability in abilities:
        prompt = ability.partial_sys_prompt()
        history = await ability.chat_history()
        tools = ability.registered_tools()

        system_prompt += prompt
        chat_history_examples += history
        all_tools += tools

    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=['sys_prompt'], template='{sys_prompt}')),
            MessagesPlaceholder(variable_name='chat_history', optional=True),
            HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
            MessagesPlaceholder(variable_name='agent_scratchpad'),
        ],
        partial_variables={
            'sys_prompt': system_prompt,
        },
        chat_history=chat_history_examples,
    )
    agent = OpenAIFunctionsAgent(llm=llm, tools=all_tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools) #, verbose=True)

    return RunnableWithMessageHistory(
        agent_executor,
        FileChatMessageHistory,
        input_messages_key='input',
        history_messages_key='chat_history',
    )

async def main_development():
    agent = await get_ai(abilities=[
        HomeAssistantAbility(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url=os.getenv('HOMEASSISTANT_URL')),
        GoogleCalendarAbility(),
        GoogleSearchAbility(google_api_key=os.getenv('GOOGLE_API_KEY'), google_cse_id=os.getenv('GOOGLE_CSE_ID')),
        GoogleTasksAbility(),
        MovieSearchAbility(api_key=os.getenv('TMDB_API_KEY')),
        WikipediaAbility(),
        MatrixSendMessageAbility(),
    ])

    while True:
        print('\n>>> ', end='')
        str_input = input()
        print(await agent.ainvoke({'input': str_input}, config={'configurable': {'session_id': 'history_debug.db'}}))

    # await agent.ainvoke({'input': 'toggle the office lights'}, config={'configurable': {'session_id': 'history_debug.db'}})
    # await agent.ainvoke({'input': 'list my google calendar events today'}, config={'configurable': {'session_id': 'history_debug.db'}})
    # await agent.ainvoke({'input': 'create an event "do the dishes", today at 4pm'}, config={'configurable': {'session_id': 'history_debug.db'}})
    # await agent.ainvoke({'input': 'list all my TODOs'}, config={'configurable': {'session_id': 'history_debug.db'}})
    # await agent.ainvoke({'input': 'remember me to "marcar gympass" tomorrow'}, config={'configurable': {'session_id': 'history_debug.db'}})
    # await agent.ainvoke({'input': 'tell me more about the dawn of the chicken nugget movie, and where can I watch it'}, config={'configurable': {'session_id': 'history_debug.db'}})


if __name__ == '__main__':
    asyncio.run(main_development())
