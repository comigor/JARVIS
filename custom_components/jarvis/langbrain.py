from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
import os
import asyncio

from abilities.homeassistant import HomeAssistantControlEntitiesTool, HomeAssistantGetEntityTool, HomeAssistantTurnOnLightsTool
from abilities.stocks import CurrentStockPriceTool, StockPerformanceTool
from abilities.google import GoogleSearchTool
from abilities.python_repl import PythonREPLTool

async def main_development():
    llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.1)
    tools = [
        GoogleSearchTool,
        PythonREPLTool,
        CurrentStockPriceTool(),
        StockPerformanceTool(),
        HomeAssistantControlEntitiesTool(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url=os.getenv('HOMEASSISTANT_URL')),
        HomeAssistantGetEntityTool(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url=os.getenv('HOMEASSISTANT_URL')),
        HomeAssistantTurnOnLightsTool(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url=os.getenv('HOMEASSISTANT_URL')),
    ]
    agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)
    await agent.arun(
        "today is 2023-12-20. what was the biggest news yesterday?"
    )


if __name__ == '__main__':
    asyncio.run(main_development())
