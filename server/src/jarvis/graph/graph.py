from typing import List, Any, Optional, Literal, Callable, Awaitable
from datetime import datetime
import uuid

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph

from jarvis.graph.types import AgentState
from jarvis.graph.compressor_chain import (
    retrieve_filtered_chat_history,
    get_summary,
    persist_history,
)


def make_system_prompt() -> SystemMessage:
    return SystemMessage(
        content=f"""Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes functions succinctly. You are observant of all the details in the data you have in order to come across as highly observant, emotionally intelligent and humanlike in your responses, always trying to use less than 30 words in the language user has asked.

Answer the user's questions about the world truthfully. Be careful not to execute functions if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Always remember to use tools to make sure you're doing the best you can. So when you need to know what day or what time is it, for example, use a Python shell. For tools related to Home control, always list all entities first, to avoid using non-existent entities.

Use metric system and Celsius.

Right now is {datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Consider local holidays and treat them as non-work days.

Think and execute tools in English, but always answer in brazilian portuguese."""
    )


store: dict[str, List[BaseMessage]] = {}


def get_session_history(session_id: str) -> List[BaseMessage]:
    if session_id not in store:
        store[session_id] = []
    return store[session_id]


def generate_graph(
    llm: BaseChatModel,
    tools: List[BaseTool],
) -> CompiledGraph:
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}

    def _invoke_tool(tool_call: Any):
        return ToolMessage(
            content=tool_map[tool_call["name"]].invoke(input=tool_call["args"]),
            tool_call_id=tool_call["id"],
        )

    async def _ainvoke_tool(tool_call: Any):
        return ToolMessage(
            content=await tool_map[tool_call["name"]].ainvoke(input=tool_call["args"]),
            tool_call_id=tool_call["id"],
        )

    tool_executor = RunnableLambda(_invoke_tool, _ainvoke_tool)

    async def should_call_tools(
        state: AgentState, _config: Optional[RunnableConfig] = None
    ) -> Literal["yes", "no"]:
        last_msg = state.messages[-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "yes"
        return "no"

    async def call_agent(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentState:
        message_to_append = await llm_with_tools.ainvoke(
            [
                *state.system_messages,
                *state.messages,
            ],
            config=config,
        )
        return state.copy_with(
            append_messages=[message_to_append],
        )

    async def call_tools(
        state: AgentState, _config: Optional[RunnableConfig] = None
    ) -> AgentState:
        last_msg = state.messages[-1]
        tools_return = []
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            tools_return = await tool_executor.abatch(last_msg.tool_calls)

        return state.copy_with(
            append_messages=list(tools_return),
        )

    async def assoc_history(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentState:
        session_id = (
            (config or {}).get("configurable", {}).get("session_id", "fallback")
        )
        if session_id in store:
            # Do not retrieve history again, as messages will be populated
            return state

        return state.copy_with(
            replace_filtered_chat_history=await retrieve_filtered_chat_history(),
        )

    def assoc_summary(
        llm: BaseChatModel,
    ) -> Callable[[AgentState], Awaitable[AgentState]]:
        async def _assoc_summary(
            state: AgentState, config: Optional[RunnableConfig] = None
        ) -> AgentState:
            return state.copy_with(
                append_system_messages=await get_summary(
                    llm, state.filtered_chat_history, config
                ),
            )

        return _assoc_summary

    async def assoc_messages(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentState:
        session_id = (
            (config or {}).get("configurable", {}).get("session_id", "fallback")
        )
        return state.copy_with(
            append_messages=[
                *store.get(session_id, []),
                HumanMessage(content=state.question, id=str(uuid.uuid4())),
            ],
        )

    async def persist_messages(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentState:
        await persist_history([*state.filtered_chat_history, *state.messages])
        session_id = (
            (config or {}).get("configurable", {}).get("session_id", "fallback")
        )
        store[session_id] = list(state.messages)
        return state

    workflow = StateGraph(AgentState)
    workflow.add_node("assoc_history", assoc_history)
    workflow.add_node("assoc_summary", assoc_summary(llm))
    workflow.add_node("assoc_messages", assoc_messages)
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", call_tools)
    workflow.add_node("persist_messages", persist_messages)

    workflow.set_entry_point("assoc_history")

    workflow.add_edge("assoc_history", "assoc_summary")
    workflow.add_edge("assoc_summary", "assoc_messages")
    workflow.add_edge("assoc_messages", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_call_tools,
        {
            "yes": "tools",
            "no": "persist_messages",
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("persist_messages", END)

    # memory = AsyncSqliteSaver.from_conn_string("chat_history.db")
    graph = workflow.compile(debug=True)  # , checkpointer=memory)
    return graph
