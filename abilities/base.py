from abc import ABC, abstractmethod
from kani import AIFunction, ChatMessage

class BaseAbility(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def sys_prompt(self) -> str:
        ...

    @abstractmethod
    def chat_history(self) -> [ChatMessage]:
        ...

    @abstractmethod
    def registered_functions(self) -> [AIFunction]:
        ...
