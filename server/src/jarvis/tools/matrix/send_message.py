import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from nio import RoomSendResponse

_LOGGER = logging.getLogger(__name__)


class MatrixSendMessageInput(BaseModel):
    room_name: str = Field(
        description="Name of the room, group or person you want to send the message to."
    )
    message: str = Field(
        description="Message content."
    )


class MatrixSendMessageTool(BaseTool):
    name = "matrix_send_message"
    description = "Send a message to a room, group or person."
    args_schema: Type[BaseModel] = MatrixSendMessageInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, room_name: str, message: str) -> str:
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, room_name: str, message: str) -> str:
        from jarvis.tools.matrix.base import client
        if client:
            room_info = client.find_room_id_by_name(room_name)
            if room_info:
                resp = await client.send_message(room_info["id"], message)

                return (
                    "Message sent successfully."
                    if isinstance(resp, RoomSendResponse)
                    else f"Sorry, I can't do that."
                )
        return "Sorry, I can't do that."
