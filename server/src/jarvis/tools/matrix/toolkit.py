from typing import List
from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_core.tools import BaseTool

from jarvis.tools.matrix.send_message import MatrixSendMessageTool

class MatrixToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        return [
            MatrixSendMessageTool(),
        ]
