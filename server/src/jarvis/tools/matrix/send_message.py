import logging
import json
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
        import asyncio
        # loop = asyncio.get_running_loop()
        # loop = asyncio.new_event_loop()
        # a = asyncio.run_coroutine_threadsafe(self._arun(room_name, message), loop)
        # return a.result()
        return asyncio.create_task(self._arun(room_name, message)).result()
        # return asyncio.run(self._arun(room_name, message))

    async def _arun(self, room_name: str, message: str) -> str:
        from jarvis.tools.matrix.base import client
        if client:
            room_info = client.find_room_id_by_name(room_name)
            if room_info:
                resp = await client.send_message(room_info["id"], message)
                a = 0

        # _LOGGER.debug(f"Matrix.sendMessage: client {client}, room_info {room_info}, resp {resp}")

        return (
            "Message sent successfully."
            if isinstance(resp, RoomSendResponse)
            else f"Sorry, I can't do that."
        )
