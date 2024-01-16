from abc import ABC, abstractmethod
from typing import List
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

class BaseAbility(ABC):
    @abstractmethod
    def partial_sys_prompt(self) -> str:
        ...

    @abstractmethod
    async def chat_history(self) -> List[BaseMessage]:
        ...

    @abstractmethod
    def registered_tools(self) -> List[BaseTool]:
        ...
