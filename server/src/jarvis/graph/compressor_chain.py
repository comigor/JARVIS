from typing import Optional, List
import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import messages_from_dict
from langchain_core.messages.base import messages_to_dict
from langchain_core.runnables.config import RunnableConfig


summaries_cache: dict[str, List[BaseMessage]] = {}


async def _call_llm(
    llm: BaseChatModel,
    filtered_chat_history: List[BaseMessage],
    config: Optional[RunnableConfig] = None,
) -> BaseMessage:
    return await llm.ainvoke(
        input=[
            # SystemMessage(
            #     content="You are a writer specialized in creating good summaries of conversations."
            # ),
            *filtered_chat_history,
            SystemMessage(
                content=(
                    "Summarize this conversation so far in less than 100 words, in English. "
                    "Make sure to state all relevant facts from the user. Assume your last message is correct."
                ),
            ),
        ],
        config=config,
    )


async def retrieve_filtered_chat_history() -> List[BaseMessage]:
    filtered_chat_history = []
    try:
        with open("chat_history.json", "r") as file:
            filtered_chat_history = messages_from_dict(json.loads(file.read()))
    except Exception:
        ...

    return filtered_chat_history


async def get_summary(
    llm: BaseChatModel,
    filtered_chat_history: List[BaseMessage],
    config: Optional[RunnableConfig] = None,
) -> List[BaseMessage]:
    if len(filtered_chat_history) == 0:
        return []

    session_id = (config or {}).get("configurable", {}).get("session_id", "fallback")
    if session_id not in summaries_cache:
        session_id = (
            (config or {}).get("configurable", {}).get("session_id", "fallback")
        )
        response = await _call_llm(llm, filtered_chat_history, config)
        summaries_cache[session_id] = [
            SystemMessage(
                content=f"""Consider the following conversation context:\n{response.content}"""
            ),
        ]

    return summaries_cache[session_id]


async def persist_history(full_chat_history: List[BaseMessage]) -> None:
    deduped = [
        i for n, i in enumerate(full_chat_history) if i not in full_chat_history[:n]
    ]

    filtered_messages = list(
        filter(
            lambda m: isinstance(m, HumanMessage)
            or (isinstance(m, AIMessage) and len(m.tool_calls) == 0),
            deduped,
        )
    )

    with open("chat_history.json", "w") as file:
        file.write(json.dumps(messages_to_dict(filtered_messages)))
