from langchain.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from typing import List
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from .base import BaseAbility

class WikipediaAbility(BaseAbility):
    def partial_sys_prompt(self) -> str:
        return ""

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        return [
            WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
        ]
