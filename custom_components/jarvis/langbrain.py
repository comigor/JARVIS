from langchain.agents import AgentExecutor, OpenAIFunctionsAgent
from langchain.chat_models import ChatOpenAI
# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ChatMessage, FunctionMessage, ToolMessage
from langchain_core.prompts.chat import MessagesPlaceholder, SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import os
import asyncio

from abilities.stocks import CurrentStockPriceTool, StockPerformanceTool
from abilities.homeassistant import HomeAssistantAbility
from abilities.google import GoogleSearchTool
from abilities.python_repl import PythonREPLTool

from langchain_core.prompts import ChatPromptTemplate

from abilities.base import BaseAbility

async def get_ai(abilities: [BaseAbility]) -> AgentExecutor:
    llm = ChatOpenAI(model='gpt-3.5-turbo-1106', temperature=0.2)

    system_prompt = ''
    chat_history = []
    all_tools = [
        GoogleSearchTool,
        PythonREPLTool,
        CurrentStockPriceTool(),
        StockPerformanceTool(),
    ]

    for ability in abilities:
        prompt = ability.partial_sys_prompt()
        history = await ability.chat_history()
        tools = ability.registered_tools()

        system_prompt += prompt
        chat_history += history
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
    )
    # prompt = ChatPromptTemplate.from_messages([('system', 'You are a helpful assistant'),])
    agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    message_history = ChatMessageHistory(messages=chat_history)

    return RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: message_history,
        input_messages_key='input',
        history_messages_key='chat_history',
    )


async def main_development():
    agent = await get_ai(abilities=[
        HomeAssistantAbility(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url=os.getenv('HOMEASSISTANT_URL')),
    ])
    await agent.ainvoke({'input': 'toggle the office lights'}, config={'configurable': {'session_id': '<foo>'}})

if __name__ == '__main__':
    asyncio.run(main_development())
