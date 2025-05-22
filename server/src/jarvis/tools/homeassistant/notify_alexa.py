import logging
import json
from typing import Type
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantNotifyAlexaInput(BaseModel):
    message: str = Field(
        description="The message of the notification"
    )
    target: str = Field(
        description="The entity IDs of target device to send the notification to, e.g. media_player.igor_s_echo_dot"
    )


class HomeAssistantNotifyAlexaTool(HomeAssistantBaseTool):
    name: str = "home_assistant_notify_alexa"
    description: str = "Useful when you want to send/display/ring notification using Alexa, notify in real time."
    args_schema: Type[BaseModel] = HomeAssistantNotifyAlexaInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, message: str, target: str) -> str:
        self.client.post(
            f"{self.base_url}/api/services/media_player/play_media",
            headers=self.headers,
            json={
                "entity_id": target,
                "media_content_type": "sound",
                "media_content_id": "bell_02",
            },
        )
        response = self.client.post(
            f"{self.base_url}/api/services/notify/alexa_media",
            headers=self.headers,
            json={
                "message": message,
                "target": target,
            },
        )
        json_obj = response.json()
        _LOGGER.debug(json_obj)
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
