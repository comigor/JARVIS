from typing import List
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from langchain.tools.google_search.tool import GoogleSearchRun
from langchain.utilities.google_search import GoogleSearchAPIWrapper

from ..base import BaseAbility

class GoogleSearchAbility(BaseAbility):
    def __init__(self, google_api_key: str, google_cse_id: str, **kwds):
        super(GoogleSearchAbility, self).__init__(**kwds)
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id

    def partial_sys_prompt(self) -> str:
        return ""

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        return [
            GoogleSearchRun(api_wrapper=GoogleSearchAPIWrapper(google_api_key=self.google_api_key, google_cse_id=self.google_cse_id)),
        ]
