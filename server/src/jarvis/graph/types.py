from typing import List
from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class AgentState(BaseModel):
    filtered_chat_history: List[BaseMessage] = []
    system_messages: List[BaseMessage] = []
    messages: List[BaseMessage] = []
    question: str

    def copy_with(
        self: "AgentState",
        append_messages: List[BaseMessage] = [],
        replace_filtered_chat_history: List[BaseMessage] = [],
        append_system_messages: List[BaseMessage] = [],
    ) -> "AgentState":
        return AgentState(
            filtered_chat_history=replace_filtered_chat_history
            or self.filtered_chat_history,
            system_messages=[*self.system_messages, *append_system_messages],
            messages=[*self.messages, *append_messages],
            question=self.question or self.question,
        )
