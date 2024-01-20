from pathlib import Path
from abc import ABC, abstractmethod
from typing import List
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from const import ROOT_DIR

def get_full_file_path(relative_path: str) -> str:
    path = Path(ROOT_DIR).joinpath(relative_path)
    if not path.is_file() and not path.is_dir():
        path2 = Path(ROOT_DIR).parent.joinpath(relative_path)
        if not path2.is_file() and not path2.is_dir():
            raise Exception(f'Could not find file: {relative_path}. Tried {path} & {path2}.')
        return str(path2)
    return str(path)


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
