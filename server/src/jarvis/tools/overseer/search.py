import json
import logging
from typing import Type
from pydantic import BaseModel, Field

from jarvis.tools.overseer.base import OverseerBaseTool

_LOGGER = logging.getLogger(__name__)


class OverseerSearchSchema(BaseModel):
    query: str = Field(description="The search query.")


class OverseerSearchTool(OverseerBaseTool):
    name: str = "overseer_search"
    description: str = "Returns a list of movies or TV shows and their information given a search query."
    args_schema: Type[BaseModel] = OverseerSearchSchema

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, query: str) -> str:
        response = self.client.get(
            f"{self.base_url}/api/v1/search?query={query}&page=1&language=en",
            headers=self.headers,
        )
        json_obj = list(
            map(
                lambda s: {
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "overview": s.get("overview"),
                    "popularity": s.get("popularity"),
                    "releaseDate": s.get("releaseDate"),
                    "voteAverage": s.get("voteAverage"),
                },
                response.json().get("results", []),
            )
        )
        _LOGGER.debug(json_obj)
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
