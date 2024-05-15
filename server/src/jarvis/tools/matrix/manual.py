import asyncio
import json
import os
import sys
import aiofiles

from nio import (
    AsyncClient,
    AsyncClientConfig,
    InviteEvent,
    LoginResponse,
    MatrixRoom,
    RoomMessageText,
    RoomNameEvent,
    RoomTopicEvent,
    MegolmEvent,
    RoomKeyRequest,
    Event,
    KeyVerificationCancel,
    KeyVerificationEvent,
    KeyVerificationKey,
    KeyVerificationMac,
    KeyVerificationStart,
    KeyVerificationAccept,
    ToDeviceError,
    LocalProtocolError,
    JoinedRoomsResponse,
)

SESSION_DETAILS_FILE = "credentials2.json"
STORE_FOLDER = "store2"
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

        # if the store location doesn't exist, we'll make it
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)

        # self.add_event_callback(self.cb_autojoin_room, InviteEvent)
        self.add_event_callback(self.cb_print_messages, RoomMessageText)
        # self.add_event_callback(self.olm_callback, MegolmEvent)
        # self.add_event_callback(self.all_events, Event)
        def key_share_cb(event: RoomKeyRequest):
            user_id = event.sender
            device_id = event.requesting_device_id
            device = self.device_store[user_id][device_id]
            self.verify_device(device)
            for request in self.get_active_key_requests(
                user_id, device_id):
                self.continue_key_share(request)
        self.add_to_device_callback(key_share_cb, (RoomKeyRequest,))
        self.add_to_device_callback(self.key_verif, (KeyVerificationCancel,
        KeyVerificationEvent,
        KeyVerificationKey,
        KeyVerificationMac,
        KeyVerificationStart,
        KeyVerificationAccept,))

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

    async def olm_callback(self, room: MatrixRoom, event: MegolmEvent):
        # print(f"Encrypted: {repr(event)}")
        try:
            await self.request_room_key(event)
        except Exception as e:
            print(f"Error while request keys: {repr(e)}")

    def all_events(self, room: MatrixRoom, event: Event):
        print(f"event {repr(event)}")
        # self.rooms[room.room_id] = room
        ...

    async def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        """Callback to automatically joins a Matrix room on invite.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {InviteEvent} -- Provided by nio
        """
        await self.join(room.room_id)
        # room = self.rooms[room.room_id]
        print(f"Room {room.name} is encrypted: {room.encrypted}")

    async def cb_print_messages(self, room: MatrixRoom, event: RoomMessageText):
        """Callback to print all received messages to stdout.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {RoomMessageText} -- Provided by nio
        """
        if event.decrypted:
            encrypted_symbol = "🛡 "
        else:
            encrypted_symbol = "⚠️ "
        print(
            f"{room.display_name} |{encrypted_symbol}| {room.user_name(event.sender)}: {event.body}"
        )

        if event.body == '!full_sync' and event.sender == '@borges:beeper.com':
            joined = await self.joined_rooms()
            if isinstance(joined, JoinedRoomsResponse):
                for r_id in joined.rooms:
                    self.rooms[r_id] = MatrixRoom(r_id, self.user_id, True)
                    # ddd = await self.room_get_state(r_id)
                    # print(ddd)
                self.next_batch = None
                self.loaded_sync_token = None
                synced = await self.sync(full_state=True) # force full sync, with since=""
                a = 10
        elif event.body == '!ping' and event.sender == '@borges:beeper.com':
            await self.send_message(room.room_id, 'pong!')

    async def key_verif(self, event):  # noqa
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

                resp = await client.confirm_short_auth_string(event.transaction_id)
                if isinstance(resp, ToDeviceError):
                    print(f"confirm_short_auth_string failed with {resp}")

                # yn = input("Do the emojis match? (Y/N) (C for Cancel) ")
                # if yn.lower() == "y":
                #     print(
                #         "Match! The verification for this " "device will be accepted."
                #     )
                #     resp = await client.confirm_short_auth_string(event.transaction_id)
                #     if isinstance(resp, ToDeviceError):
                #         print(f"confirm_short_auth_string failed with {resp}")
                # elif yn.lower() == "n":  # no, don't match, reject
                #     print(
                #         "No match! Device will NOT be verified "
                #         "by rejecting verification."
                #     )
                #     resp = await client.cancel_key_verification(
                #         event.transaction_id, reject=True
                #     )
                #     if isinstance(resp, ToDeviceError):
                #         print(f"cancel_key_verification failed with {resp}")
                # else:  # C or anything for cancel
                #     print("Cancelled by user! Verification will be " "cancelled.")
                #     resp = await client.cancel_key_verification(
                #         event.transaction_id, reject=False
                #     )
                #     if isinstance(resp, ToDeviceError):
                #         print(f"cancel_key_verification failed with {resp}")

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

    async def send_message(self, room_id, message):
        try:
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

async def run_client(client: CustomEncryptedClient) -> None:
    """A basic encrypted chat application using nio."""

    await client.login()

    # await client.sync(full_state=True)
    # await client.synced.wait()

    # await client.import_keys('element-keys.txt', input("Please input keys password: "))
    await client.sync_forever(timeout=30000, full_state=True)
    # await client.send_message("!NZLViIsAXbmQ6zDGOs20:beeper.local", "hello world")

async def main():
    config = AsyncClientConfig(store_sync_tokens=True)
    client = CustomEncryptedClient(
        homeserver="https://matrix.beeper.com",
        user="@borges:beeper.com",
        device_id='matrix-nio',
        store_path=STORE_FOLDER,
        config=config,
    )

    try:
        await run_client(client)
    except (asyncio.CancelledError, KeyboardInterrupt):
        ...
    await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
