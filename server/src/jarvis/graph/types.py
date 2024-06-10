import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    full_chat_history: Sequence[BaseMessage]
    compressed_context: Sequence[BaseMessage]
    messages: Annotated[Sequence[BaseMessage], operator.add]
