from typing import List, Any, Optional
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from langchain_core.tools import BaseTool
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.graph import CompiledGraph
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Sequence, Literal
from langchain_core.messages import BaseMessage

from jarvis.graph.types import AgentState
from jarvis.graph.compressor_chain import compressor_chain


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

    async def should_continue(
        state: AgentState, _config: Optional[RunnableConfig] = None
    ) -> Literal["tools", "__end__"]:
        last_msg = state["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "tools"
        return "__end__"

    def _state_with_new_messages(
        state: AgentState, messages_to_append: Sequence[BaseMessage]
    ) -> AgentState:
        return {
            "full_chat_history": state["full_chat_history"],
            "compressed_context": state["compressed_context"],
            "messages": messages_to_append,
        }

    async def call_model(
        state: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentState:
        return _state_with_new_messages(
            state,
            messages_to_append=[
                await llm_with_tools.ainvoke(
                    [
                        *state["compressed_context"],
                        *state["messages"],
                    ],
                    config=config,
                ),
            ],
        )

    async def call_tools(
        state: AgentState, _config: Optional[RunnableConfig] = None
    ) -> AgentState:
        last_msg = state["messages"][-1]
        tools_return = []
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            tools_return = await tool_executor.abatch(last_msg.tool_calls)

        return _state_with_new_messages(state, messages_to_append=tools_return)

    workflow = StateGraph(AgentState)
    workflow.add_node("generate_context", compressor_chain(llm))
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)

    workflow.set_entry_point("generate_context")

    workflow.add_edge("generate_context", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )
    workflow.add_edge("tools", "agent")
    graph = workflow.compile(debug=True)
    return graph
