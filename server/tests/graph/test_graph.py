import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
from datetime import datetime

# Ensure imports from jarvis are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from jarvis.graph.graph import (
    make_system_prompt, 
    generate_graph,
    # Individual node functions for direct testing if needed, or test via graph execution trace
    # For now, we'll focus on generate_graph structure and mock node internals where complex
)
from jarvis.graph.types import AgentState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph # For isinstance check

class TestGraph(unittest.IsolatedAsyncioTestCase):

    def test_make_system_prompt(self):
        prompt = make_system_prompt()
        self.assertIsInstance(prompt, SystemMessage)
        self.assertIn("J.A.R.V.I.S.", prompt.content)
        # Check if current date is in the prompt (format might vary, so check for year or a known part)
        self.assertIn(datetime.now().strftime("%Y-%m-%d"), prompt.content)

    @patch('jarvis.graph.graph.retrieve_filtered_chat_history', new_callable=AsyncMock)
    @patch('jarvis.graph.graph.get_summary', new_callable=AsyncMock)
    @patch('jarvis.graph.graph.persist_history', new_callable=AsyncMock)
    @patch('jarvis.graph.graph.llm') # Mock the llm module-level variable if used directly by nodes
    @patch.object(BaseChatModel, 'bind_tools', return_value=MagicMock(spec=BaseChatModel)) # Mock bind_tools
    @patch.object(BaseChatModel, 'ainvoke', new_callable=AsyncMock) # Mock ainvoke for agent node
    def test_generate_graph_structure_and_nodes(self, mock_llm_ainvoke, mock_bind_tools, mock_llm_module, 
                                               mock_persist_history, mock_get_summary, mock_retrieve_filtered_history):
        
        mock_llm_instance = MagicMock(spec=BaseChatModel)
        # mock_llm_module.return_value = mock_llm_instance # If llm is used as from jarvis.graph.graph import llm
        
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "test_tool"
        
        # Mock return values for node functions
        mock_retrieve_filtered_history.return_value = [HumanMessage(content="historical")]
        mock_get_summary.return_value = [SystemMessage(content="summary")]
        
        # Mock agent's response
        ai_response_with_tools = AIMessage(content="AI says something", tool_calls=[{"name": "test_tool", "args": {}, "id": "tool_123"}])
        ai_response_no_tools = AIMessage(content="AI says something final")
        
        # Side effect for llm.ainvoke to simulate different agent responses
        mock_llm_ainvoke.side_effect = [ai_response_with_tools, ai_response_no_tools]

        # Mock tool executor if call_tools is tested deeply (for now, assume it works if agent produces tool_calls)
        # Mocking the tool_executor directly if it's an object, or its call if it's a function
        # For this test, we'll focus on the agent producing tool calls or not.

        graph_instance = generate_graph(mock_llm_instance, [mock_tool])
        self.assertIsInstance(graph_instance.graph, StateGraph)

        # Check if nodes are present
        self.assertIn("assoc_history", graph_instance.graph.nodes)
        self.assertIn("assoc_summary", graph_instance.graph.nodes)
        self.assertIn("assoc_messages", graph_instance.graph.nodes)
        self.assertIn("agent", graph_instance.graph.nodes)
        self.assertIn("tools", graph_instance.graph.nodes)
        self.assertIn("persist_messages", graph_instance.graph.nodes)

        # Test conditional edge logic (simplified)
        # This requires a deeper integration test or very careful mocking of state transitions.
        # For now, we confirm that the 'agent' node can lead to 'tools' or 'persist_messages'.
        
        # Test a simple run through the graph (conceptual)
        # This would involve invoking the graph with an initial state and checking the output state
        # or intermediate node calls. This is complex to do without running parts of the graph.
        
        # Example of testing a node function in isolation (if they were easily importable/callable)
        # e.g., test `should_call_tools`
        # from jarvis.graph.graph import should_call_tools # Assuming it's importable
        # self.assertEqual(await should_call_tools(AgentState(messages=[ai_response_with_tools], question="q")), "yes")
        # self.assertEqual(await should_call_tools(AgentState(messages=[ai_response_no_tools], question="q")), "no")

    # More detailed tests for each node function could be added here,
    # mocking their specific inputs and outputs if the generate_graph test becomes too complex.

    # Test for `should_call_tools` (example of testing a component used by the graph)
    async def test_should_call_tools_logic(self):
        # This function is defined inside generate_graph, so we test its logic conceptually
        # or by invoking the compiled graph with specific states.
        # For a direct test, it would need to be refactored out or tested via graph execution.

        # Test case: AI message with tool calls
        state_with_tools = AgentState(
            messages=[AIMessage(content="Tool time", tool_calls=[{"name": "a", "args": {}, "id": "1"}])],
            question="test"
        )
        # In a real graph execution, this would be `graph.nodes['agent'].invoke(state_with_tools)`
        # then the conditional edge would evaluate `should_call_tools`.
        # If `should_call_tools` were standalone:
        # self.assertEqual(await should_call_tools(state_with_tools), "yes")

        # Test case: AI message without tool calls
        state_no_tools = AgentState(
            messages=[AIMessage(content="No tools needed")],
            question="test"
        )
        # If `should_call_tools` were standalone:
        # self.assertEqual(await should_call_tools(state_no_tools), "no")
        pass # Placeholder as direct test of should_call_tools is hard due to scope

if __name__ == '__main__':
    unittest.main()
