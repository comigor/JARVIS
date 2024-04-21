import operator
from typing import Annotated, Sequence, TypedDict, List, Any, Optional
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from langchain_core.runnables import RunnableLambda, Runnable
from langgraph.graph import END, StateGraph
from langchain_core.language_models import LanguageModelInput
from langchain_core.tools import BaseTool
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.graph import CompiledGraph


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


def generate_graph(
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
    tools: List[BaseTool],
) -> CompiledGraph:
    def _invoke_tool(tool_call: Any):
        tool = {tool.name: tool for tool in tools}[tool_call["name"]]
        return ToolMessage(
            content=tool.invoke(input=tool_call["args"]),
            tool_call_id=tool_call["id"],
        )

    tool_executor = RunnableLambda(_invoke_tool)

    def should_continue(state: AgentState):
        last_msg = state["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "continue"
        return "end"

    def call_model(state: AgentState, config: Optional[RunnableConfig] = None):
        return {"messages": [llm_with_tools.invoke(state["messages"], config=config)]}

    def call_tools(state: AgentState):
        last_msg = state["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return {"messages": tool_executor.batch(last_msg.tool_calls)}
        return {"messages": []}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tools)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END,
        },
    )
    workflow.add_edge("action", "agent")
    graph = workflow.compile()
    return graph
