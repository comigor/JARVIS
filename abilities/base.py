from abc import ABC, abstractmethod
from kani import AIFunction, ChatMessage
from typing import List

class BaseAbility(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def sys_prompt(self) -> str:
        ...

    @abstractmethod
    async def chat_history(self) -> List[ChatMessage]:
        ...

    @abstractmethod
    def registered_functions(self) -> List[AIFunction]:
        ...
