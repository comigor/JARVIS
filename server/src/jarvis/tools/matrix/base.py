import asyncio, logging, json, re, aiofiles
from nio import AsyncClient, AsyncClientConfig, RoomKeyRequest, MegolmEvent
from fuzzywuzzy import fuzz

from ..base import get_full_file_path

json_fname = 'jarvis-config/rooms.json'
CONFIG_FILE = 'jarvis-config/credentials.json'  # login credentials JSON file
STORE_PATH = 'jarvis-config/store/'  # local directory
_LOGGER = logging.getLogger(__name__)

def force_key_share(client: AsyncClient):
    for request in client.get_active_key_requests(client.user_id, client.device_id):
        client.continue_key_share(request)

async def authenticate_with_matrix():
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=True,
    )

    # open the file in read-only mode
    async with aiofiles.open(get_full_file_path(CONFIG_FILE), "r") as f:
        contents = await f.read()
    config = json.loads(contents)
    # Initialize the matrix client based on credentials from file
    client = AsyncClient(
        config["homeserver"],
        config["user_id"],
        device_id=config["device_id"],
        store_path=get_full_file_path(STORE_PATH),
        config=client_config,
    )

    client.restore_login(
        user_id=config["user_id"],
        device_id=config["device_id"],
        access_token=config["access_token"],
    )
    print("Logged in using stored credentials.")

    def key_share_cb(event: RoomKeyRequest):
        user_id = event.sender
        device_id = event.requesting_device_id
        device = client.device_store[user_id][device_id]
        client.verify_device(device)
        force_key_share(client)

    client.add_to_device_callback(key_share_cb, RoomKeyRequest)

    return client

async def retrieve_and_cache_rooms(client: AsyncClient):
    rooms_json = {}

    # Hacky way to _really_ sync fully
    client.next_batch = None
    client.loaded_sync_token = None
    synced = await client.sync(60000, full_state = True)

    rooms = client.rooms
    for room_id, room in rooms.items():
        names = set()
        name_hashmap = {}

        source = None
        for (name, ids) in room.names.items():
            if 'bridge bot' in name.lower():
                source = name.split()[0]
                continue
            names.add(name)
            for id in ids:
                name_hashmap[id] = name

        if (not source):
            source = room.display_name

        room_info = synced.rooms.join[room_id]

        if room_id == '!jgWE3HRXsPCOXlaCjnPS:beeper.local' or room_id == '!YCgovI5k7JLaqG8gVfkS:beeper.local':
            print(9)

        for event in room_info.timeline.events:
            if isinstance(event, MegolmEvent) and event.session_id not in client.outgoing_key_requests:
                await client.request_room_key(event)
        force_key_share(client)

        rooms_json[room_id] = {
            'id': room_id,
            'source': source,
            'names': list(names),
            'display_name': re.sub(r'(.*?)( \(@.*| and \d+ others?)?', '\\1', room.display_name),
            'unread_highlights': room.unread_highlights,
            'unread_notifications': room.unread_notifications,
            'prev_batch': room_info.timeline.prev_batch,
            'name_hashmap': name_hashmap,
            # 'messages': list(map(lambda e: f'{name_hashmap[e.sender]}: {e.body}', filter(lambda e: isinstance(e, RoomMessageText), room_info.timeline.events))),
        }

    _LOGGER.info(f"\nFound {len(rooms_json)} rooms! Writing to {json_fname}")
    with open(get_full_file_path(json_fname), 'w') as f:
        f.write(json.dumps(rooms_json, indent=4))

    _LOGGER.info(f"\nUpdated {json_fname}")
    await client.close()

    return rooms_json

def assoc_ratio(room, room_name: str):
    return {
        **room,
        'ratio': fuzz.ratio(room_name.lower(), room['display_name'].lower()),
    }

def find_room_id_by_name(rooms_json, room_name: str):
    filtered_rooms = list(filter(lambda r: r['ratio'] >= 45, map(lambda r: assoc_ratio(r, room_name), rooms_json.values())))
    sorted_rooms = sorted(filtered_rooms, key=lambda r: r['ratio'])
    return sorted_rooms[-1]

async def main_dev():
    client = await authenticate_with_matrix()
    rooms = await retrieve_and_cache_rooms(client)
    print(9)

if __name__ == '__main__':
    asyncio.run(main_dev())
