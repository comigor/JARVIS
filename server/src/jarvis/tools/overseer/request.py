import logging
from typing import Type
from pydantic import BaseModel, Field
from enum import Enum

from jarvis.tools.overseer.base import OverseerBaseTool

_LOGGER = logging.getLogger(__name__)


class MediaType(str, Enum):
    movie = "movie"
    tv = "tv"


class OverseerDownloadSchema(BaseModel):
    media_id: int = Field(
        description="The movie or TV series ID. To discover it, use overseer_search."
    )
    media_type: MediaType = Field(description="If it's a movie or TV series.")


class OverseerDownloadTool(OverseerBaseTool):
    name = "overseer_download"
    description = "Download a movie or TV series by its ID."
    args_schema: Type[BaseModel] = OverseerDownloadSchema

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, media_id: int, media_type: MediaType) -> str:
        response = self.client.post(
            f"{self.base_url}/api/v1/request",
            headers=self.headers,
            json={
                "mediaId": media_id,
                "mediaType": media_type.value,
                **({"seasons": [1]} if media_type == MediaType.tv else {}),
            },
        )
        return (
            "OK, it will be downloaded"
            if response.status_code == 201
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
