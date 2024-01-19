from typing import List, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from .base import user_id, authenticate_with_matrix, retrieve_and_cache_rooms, find_room_id_by_name
from ..base import BaseAbility

class SendMessageMatrixSchema(BaseModel):
    room_name: str = Field(description='Name of the Matrix room, group or person you want to send the message.')
    message: str = Field(description='Message content')

class SendMessageMatrixTool(BaseTool):
    name = 'send_message_matrix_tool'
    description = 'Send a message in a Matrix server room'
    args_schema: Type[BaseModel] = SendMessageMatrixSchema
    
    async def _arun(self, room_name: str, message: str):
        client = await authenticate_with_matrix()

        try:
            rooms = await retrieve_and_cache_rooms(client)
            room = find_room_id_by_name(rooms, room_name)

            # Join the room (if not already joined)
            await client.room_invite(room['id'], user_id)
            await client.join(room['id'])

            # Send the message
            await client.room_send(
                room['id'],
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message},
            )

            return f"Message sent to Matrix room {room['id']}.", None

        except Exception as e:
            error_str = str(e)
            return None, error_str

    def _run(self, room_name: str, message: str):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

class MatrixSendMessageAbility(BaseAbility):
    def partial_sys_prompt(self) -> str:
        return ''

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        # Return instances of the tools you want to register
        return [SendMessageMatrixTool()]