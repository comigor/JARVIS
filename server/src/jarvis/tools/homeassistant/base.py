import httpx
from pydantic import Field
from langchain_core.tools import BaseTool


class HomeAssistantBaseTool(BaseTool):
    client: httpx.Client = Field(default_factory=lambda: httpx.Client(timeout=45))
    base_url: str = Field(default_factory=lambda: "")
    headers: dict = Field(default_factory=lambda: {})

    def __init__(self, api_key: str, base_url: str, **kwds):
        super(HomeAssistantBaseTool, self).__init__(**kwds)
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
