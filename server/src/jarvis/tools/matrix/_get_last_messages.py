import logging
from typing import List, Type
from pydantic import BaseModel, Field
from nio import AsyncClient, RoomMessageText, MegolmEvent
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from .base import authenticate_with_matrix, retrieve_and_cache_rooms, find_room_id_by_name, force_key_share
from ..base import BaseAbility
_LOGGER = logging.getLogger(__name__)

class GetLastMessagesMatrixSchema(BaseModel):
    room_name: str = Field(description='Name of the room, group or person you want to get the last messages.')

class GetLastMessagesMatrixTool(BaseTool):
    name = 'get_last_messages_matrix_tool'
    description = 'Get the last messages of a room, group or person'
    args_schema: Type[BaseModel] = GetLastMessagesMatrixSchema
    
    async def _arun(self, room_name: str):
        client: AsyncClient = await authenticate_with_matrix()
        rooms = await retrieve_and_cache_rooms(client)
        room = find_room_id_by_name(rooms, room_name)
        # aa = await client.room_messages(room['id'], room['prev_batch'], limit=100)

        response = await client.room_messages(room['id'], '', limit=50)
        for event in response.chunk:
            if isinstance(event, MegolmEvent) and event.session_id not in client.outgoing_key_requests:
                await client.request_room_key(event)

        response = await client.room_messages(room['id'], '', limit=25)
        events = response.chunk
        events.reverse()

        output = ''
        for event in events:
            if isinstance(event, RoomMessageText):
                output += f"{room['name_hashmap'][event.sender]}: {event.body}\n"
        force_key_share(client)

        return output

    def _run(self, room_name: str):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

class MatrixGetLastMessagesAbility(BaseAbility):
    def partial_sys_prompt(self) -> str:
        return '''My name in chats is Igor Borges.

Messages are in the following format: [SENDER]: [MESSAGE]

You can help with summarizing and replying to messages in a friendly, casual and conversational manner, and help user send short replies based on his suggestions of how to answer. Make sure to provide summaries of the messages as casually as possible WITHOUT just reading them out the details. Remember to mention the name of the sender and casually when each message was sent, but making sure to keep the total response as short as possible. DO NOT ask if anything else is needed or whether user wants to reply.'''

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        # Return instances of the tools you want to register
        return [GetLastMessagesMatrixTool()]
