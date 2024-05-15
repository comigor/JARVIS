#!/usr/bin/env python3

import asyncio
import getpass
import json
import os
import sys

import aiofiles

from nio import AsyncClient, LoginResponse

CONFIG_FILE = "credentials.json"

# Check out main() below to see how it's done.


def write_details_to_disk(resp: LoginResponse, homeserver) -> None:
    """Writes the required login details to disk so we can log in later without
    using a password.

    Arguments:
        resp {LoginResponse} -- the successful client login response.
        homeserver -- URL of homeserver, e.g. "https://matrix.example.org"
    """
    # open the config file in write-mode
    with open(CONFIG_FILE, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
            },
            f,
        )


from nio import (
    AsyncClient,
    MegolmEvent,
    ToDeviceEvent,
    LoginResponse,
    Event,
    MatrixRoom,
    SyncResponse,
    RoomMessageText,
    RoomKeyRequest,
    RoomKeyRequestResponse,
    Response,
)

class Callbacks:
    """Class to pass client to callback methods."""

    def __init__(self, client: AsyncClient):
        self.client = client

    def to_device_callback(self, event: ToDeviceEvent):
        print("to_device_callback")
        print(repr(event))
        a = 9

    async def event_callback(self, matrix_room: MatrixRoom, event: Event):
        print(f"event_callback {repr(matrix_room)}")
        print(repr(event))

        if isinstance(event, MegolmEvent):
            await self.client.request_room_key(event)
            # aaa = self.client.decrypt_event(event)
            # print(repr(aaa))
            ...

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        print(f"Message received in room {room.room_id}: {event.body}")

    async def olm_callback(self, room: MatrixRoom, event: MegolmEvent):
        print(f"Encrypted: {repr(event)}")
        await self.client.request_room_key(event)

    async def response_callback(self, response: Response):
        print("response_callback")
        print(repr(response))
        a = 10

# RoomKeyRequest(source={'content': {'action': 'request', 'body': {'algorithm': 'm.megolm.v1.aes-sha2', 'room_id': '!p7Jc1WGlE2cSaAWfbrEx:beeper.local', 'sender_key': 'd+RF1fIL2a1hNT8o2+xdWtPT3Qz4mKQDQmj0BaGV0mo', 'session_id': 'PcxHxb3vmJXff+lP9ze35c+l2lhy/57KlzIB1o3iFeI'}, 'request_id': 'mautrix-go_1715178164067170445_919', 'requesting_device_id': 'MAKPQDXQES'}, 'type': 'm.room_key_request', 'sender': '@borges:beeper.com'}, sender='@borges:beeper.com', requesting_device_id='MAKPQDXQES', request_id='mautrix-go_1715178164067170445_919', algorithm='m.megolm.v1.aes-sha2', room_id='!p7Jc1WGlE2cSaAWfbrEx:beeper.local', sender_key='d+RF1fIL2a1hNT8o2+xdWtPT3Qz4mKQDQmj0BaGV0mo', session_id='PcxHxb3vmJXff+lP9ze35c+l2lhy/57KlzIB1o3iFeI')

async def main() -> None:
    # If there are no previously-saved credentials, we'll use the password
    if os.path.exists(CONFIG_FILE):
        # open the file in read-only mode
        async with aiofiles.open(CONFIG_FILE, "r") as f:
            contents = await f.read()
        config = json.loads(contents)
        client = AsyncClient(config["homeserver"])

        client.access_token = config["access_token"]
        client.user_id = config["user_id"]
        client.device_id = config["device_id"]
        client.store_path = "store"

        client.load_store()

        print(client.sharing_session)

        callbacks = Callbacks(client)
        client.add_to_device_callback(callbacks.to_device_callback, (ToDeviceEvent,))
        client.add_event_callback(callbacks.event_callback, Event)
        client.add_response_callback(callbacks.response_callback)
        client.add_event_callback(callbacks.message_callback, RoomMessageText)
        client.add_event_callback(callbacks.olm_callback, MegolmEvent)

        await client.sync_forever(timeout=30000, full_state=True, loop_sleep_time=3000)

    await client.close()


asyncio.run(main())