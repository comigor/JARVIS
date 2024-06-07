from typing import Sequence, Any
import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.messages.utils import messages_from_dict
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.passthrough import RunnablePassthrough

from jarvis.graph.types import AgentState


contexts_cache = {}


def retrieve_full_chat_history(_input: AgentState) -> Sequence[BaseMessage]:
    full_chat_history = []
    with open("chat_history.json", "r") as file:
        full_chat_history = messages_from_dict(json.loads(file.read()))

    return full_chat_history


def concat_summarize_command(
    full_chat_history: Sequence[BaseMessage],
) -> Sequence[BaseMessage]:
    return [
        *full_chat_history,
        HumanMessage(
            content=(
                "Summarize our entire conversation so far in less than 100 words. "
                "Make sure to state all relevant facts."
            ),
        ),
    ]


def cache_context(llm_output: AIMessage, config: RunnableConfig) -> AIMessage:
    session_id = config.get("configurable", {}).get("session_id", "fallback")
    contexts_cache[session_id] = llm_output
    return llm_output


def to_state_again(v: dict[str, Any]) -> AgentState:
    return AgentState(
        full_chat_history=v["full_chat_history"],
        compressed_context=[
            *v["state"]["compressed_context"],
            SystemMessage(
                content=f"""Consider the following conversation context:\n{v["context_message"].content}"""
            ),
        ],
        messages=[],  # Add nothing new
    )


def compressor_chain(
    llm: BaseChatModel,
) -> Runnable[AgentState, Runnable[AgentState, AgentState]]:
    def check_cache(_state: AgentState, config: RunnableConfig) -> Runnable:
        session_id = config.get("configurable", {}).get("session_id", "fallback")

        # TODO: avoid retrieving full_chat_history 2x

        if session_id in contexts_cache:
            return {
                "state": RunnablePassthrough(),
                "full_chat_history": RunnableLambda(retrieve_full_chat_history),
                "context_message": RunnableLambda(
                    lambda _x: contexts_cache[session_id]
                ),
            } | RunnableLambda(to_state_again)
        else:
            return {
                "state": RunnablePassthrough(),
                "full_chat_history": RunnableLambda(retrieve_full_chat_history),
                "context_message": RunnableLambda(retrieve_full_chat_history)
                | RunnableLambda(concat_summarize_command)
                | llm
                | RunnableLambda(cache_context),
            } | RunnableLambda(to_state_again)

    return RunnableLambda(check_cache)
