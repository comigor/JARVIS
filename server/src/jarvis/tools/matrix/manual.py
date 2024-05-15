import asyncio
import json
import os
import sys
import aiofiles
import pickle
import re

from nio import (
    AsyncClient,
    AsyncClientConfig,
    LoginResponse,
    MatrixRoom,
    RoomMessageText,
    MegolmEvent,
    RoomKeyRequest,
    KeyVerificationCancel,
    KeyVerificationKey,
    KeyVerificationMac,
    KeyVerificationStart,
    ToDeviceError,
    LocalProtocolError,
)

SESSION_DETAILS_FILE = "matrix_credentials.json"
STORE_FOLDER = "matrix_store"
ALICE_PASSWORD = os.environ["MATRIX_PASSWORD"]

class CustomEncryptedClient(AsyncClient):
    def __init__(
        self,
        homeserver,
        user="",
        device_id="",
        store_path="",
        config=None,
        ssl=None,
        proxy=None,
    ):
        # Calling super.__init__ means we're running the __init__ method
        # defined in AsyncClient, which this class derives from. That does a
        # bunch of setup for us automatically
        super().__init__(
            homeserver,
            user=user,
            device_id=device_id,
            store_path=store_path,
            config=config,
            ssl=ssl,
            proxy=proxy,
        )
        self._register_callbacks()

    def _register_callbacks(self):
        # if the store location doesn't exist, we'll make it
        if self.store_path and not os.path.isdir(self.store_path):
            os.mkdir(self.store_path)

        self.add_event_callback(self._cb_handle_commands, RoomMessageText) # type: ignore
        self.add_to_device_callback(self._cb_share_room_key, (RoomKeyRequest,)) # type: ignore
        self.add_to_device_callback(self._cb_key_verification, (KeyVerificationCancel, KeyVerificationKey, KeyVerificationMac, KeyVerificationStart,)) # type: ignore
        self.add_event_callback(self._cb_olm, MegolmEvent) # type: ignore

    async def _cb_olm(self, room: MatrixRoom, event: MegolmEvent):
        try:
            await self.request_room_key(event)
        except Exception as e:
            print(f"Error while request keys: {repr(e)}")

    async def login(self) -> None:
        """Log in either using the global variables or (if possible) using the
        session details file.

        NOTE: This method kinda sucks. Don't use these kinds of global
        variables in your program; it would be much better to pass them
        around instead. They are only used here to minimise the size of the
        example.
        """
        # Restore the previous session if we can
        # See the "restore_login.py" example if you're not sure how this works
        if os.path.exists(SESSION_DETAILS_FILE) and os.path.isfile(
            SESSION_DETAILS_FILE
        ):
            try:
                async with aiofiles.open(SESSION_DETAILS_FILE, "r") as f:
                    contents = await f.read()
                config = json.loads(contents)
                self.access_token = config["access_token"]
                self.user_id = config["user_id"]
                self.device_id = config["device_id"]

                # This loads our verified/blacklisted devices and our keys
                self.load_store()
                print(
                    f"Logged in using stored credentials: {self.user_id} on {self.device_id}"
                )

                await self.try_load_client()

            except OSError as err:
                print(f"Couldn't load session from file. Logging in. Error: {err}")
            except json.JSONDecodeError:
                print("Couldn't read JSON file; overwriting")

        # We didn't restore a previous session, so we'll log in with a password
        if not self.user_id or not self.access_token or not self.device_id:
            # this calls the login method defined in AsyncClient from nio
            resp = await super().login(ALICE_PASSWORD)

            if isinstance(resp, LoginResponse):
                print("Logged in using a password; saving details to disk")
                self.__write_details_to_disk(resp)
            else:
                print(f"Failed to log in: {resp}")
                sys.exit(1)

    async def _cb_share_room_key(self, event: RoomKeyRequest):
        user_id = event.sender
        device_id = event.requesting_device_id
        device = self.device_store[user_id][device_id]
        self.verify_device(device)
        for request in self.get_active_key_requests(
            user_id, device_id):
            self.continue_key_share(request)

    async def _cb_key_verification(self, event: KeyVerificationCancel | KeyVerificationKey | KeyVerificationMac | KeyVerificationStart):
        """Handle events sent to device."""
        try:
            client = self
            print("to_device_callback")
            print(repr(event))

            if isinstance(event, KeyVerificationStart):
                if "emoji" not in event.short_authentication_string:
                    print(
                        "Other device does not support emoji verification "
                        f"{event.short_authentication_string}."
                    )
                    return
                resp = await client.accept_key_verification(event.transaction_id)
                if isinstance(resp, ToDeviceError):
                    print(f"accept_key_verification failed with {resp}")

                sas = client.key_verifications[event.transaction_id]

                todevice_msg = sas.share_key()
                resp = await client.to_device(todevice_msg)
                if isinstance(resp, ToDeviceError):
                    print(f"to_device failed with {resp}")

            elif isinstance(event, KeyVerificationCancel):
                print(
                    f"Verification has been cancelled by {event.sender} "
                    f'for reason "{event.reason}".'
                )

            elif isinstance(event, KeyVerificationKey):
                sas = client.key_verifications[event.transaction_id]

                print(f"{sas.get_emoji()}")

                # automatically accept the emoji codes (this is probably not a good idea!)
                resp = await client.confirm_short_auth_string(event.transaction_id)
                if isinstance(resp, ToDeviceError):
                    print(f"confirm_short_auth_string failed with {resp}")

                # instead, we should do this (but I don't want to wait for input() on the server)
                # https://matrix-nio.readthedocs.io/en/latest/examples.html#interactive-encryption-key-verification

            elif isinstance(event, KeyVerificationMac):
                sas = client.key_verifications[event.transaction_id]
                try:
                    todevice_msg = sas.get_mac()
                except LocalProtocolError as e:
                    # e.g. it might have been cancelled by ourselves
                    print(
                        f"Cancelled or protocol error: Reason: {e}.\n"
                        f"Verification with {event.sender} not concluded. "
                        "Try again?"
                    )
                else:
                    resp = await client.to_device(todevice_msg)
                    if isinstance(resp, ToDeviceError):
                        print(f"to_device failed with {resp}")
                    print(
                        f"sas.we_started_it = {sas.we_started_it}\n"
                        f"sas.sas_accepted = {sas.sas_accepted}\n"
                        f"sas.canceled = {sas.canceled}\n"
                        f"sas.timed_out = {sas.timed_out}\n"
                        f"sas.verified = {sas.verified}\n"
                        f"sas.verified_devices = {sas.verified_devices}\n"
                    )
                    print(
                        "Emoji verification was successful!\n"
                        "Hit Control-C to stop the program or "
                        "initiate another Emoji verification from "
                        "another device or room."
                    )
            else:
                print(
                    f"Received unexpected event type {type(event)}. "
                    f"Event is {event}. Event will be ignored."
                )
        except BaseException:
            print('sei la')

    async def _cb_handle_commands(self, room: MatrixRoom, event: RoomMessageText):
        if event.decrypted:
            encrypted_symbol = "🛡️"
        else:
            encrypted_symbol = "⚠️"
        print(
            f"{room.display_name} |{encrypted_symbol}| {room.user_name(event.sender)}: {event.body}"
        )

        if event.sender == '@borges:beeper.com':
            if event.body.startswith('!m'):
                match = re.match(r'^!m +(?P<room_id>!.+:[^ ]+) +(?P<message>.*)', event.body)
                if match:
                    room_id = match.group("room_id")
                    message = match.group("message")
                    await self.send_message(room_id, message)
                    await self.send_message(room.room_id, 'message sent')
            elif event.body == '!full_sync':
                await self.command_full_sync(room, event)
                await self.send_message(room.room_id, 'rooms synced')
            elif event.body == '!save':
                await self.command_save_client()
                await self.send_message(room.room_id, 'rooms saved')
            elif event.body == '!ping':
                await self.send_message(room.room_id, 'pong!')

    async def command_full_sync(self, room: MatrixRoom, event: RoomMessageText):
        self.next_batch = None
        self.loaded_sync_token = None
        await self.sync(full_state=True)
        await self.command_save_client()

    async def command_save_client(self):
        try:
            persist = {
                "rooms": self.rooms,
                "invited_rooms": self.invited_rooms,
                "encrypted_rooms": self.encrypted_rooms,
                "next_batch": self.next_batch,
                "loaded_sync_token": self.loaded_sync_token,
            }
            with open('matrix_rooms.pickle', 'wb') as file:
                pickle.dump(persist, file, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            print('Error while savings rooms to pickle')

    async def try_load_client(self):
        try:
            with open('matrix_rooms.pickle', 'rb') as file:
                persisted = pickle.load(file)
                self.rooms = persisted["rooms"]
                self.invited_rooms = persisted["invited_rooms"]
                self.encrypted_rooms = persisted["encrypted_rooms"]
                self.next_batch = persisted["next_batch"]
                self.loaded_sync_token = persisted["loaded_sync_token"]
        except:
            print('Error while loading rooms from pickle')

    async def send_message(self, room_id, message):
        try:
            # Hack: as all rooms may not be synced, but the user already knows the room_id,
            # we can do this to avoid errors when sending the message.
            # I think this is not necessary anymore now that we're persisting rooms.
            try:
                self.rooms[room_id]
            except KeyError:
                await self.join(room_id)
                room = MatrixRoom(room_id, self.user_id, True)
                # room.members_synced = True
                self.rooms[room_id] = room
                await self.sync(full_state=False)

            await self.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message,
                },
                ignore_unverified_devices=True,
            )
        except Exception as e:
            print(f"Error while sending message: {e}")

    @staticmethod
    def __write_details_to_disk(resp: LoginResponse) -> None:
        """Writes login details to disk so that we can restore our session later
        without logging in again and creating a new device ID.

        Arguments:
            resp {LoginResponse} -- the successful client login response.
        """
        with open(SESSION_DETAILS_FILE, "w") as f:
            json.dump(
                {
                    "access_token": resp.access_token,
                    "device_id": resp.device_id,
                    "user_id": resp.user_id,
                },
                f,
            )

async def main():
    try:
        config = AsyncClientConfig(store_sync_tokens=True)
        client = CustomEncryptedClient(
            homeserver="https://matrix.beeper.com",
            user="@borges:beeper.com",
            device_id='JARVIS',
            store_path=STORE_FOLDER,
            config=config,
        )
        await client.login()
        await client.sync_forever(timeout=30000, full_state=True)
    except:
        ...
    print("Saving and exiting...")
    await client.command_save_client()
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
