import asyncio, logging, json, re, aiofiles
from nio import AsyncClient, AsyncClientConfig
from fuzzywuzzy import fuzz

from ..base import get_full_file_path

json_fname = 'jarvis-config/rooms.json'
CONFIG_FILE = 'jarvis-config/credentials.json'  # login credentials JSON file
STORE_PATH = 'jarvis-config/store/'  # local directory
_LOGGER = logging.getLogger(__name__)

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

    return client

async def retrieve_and_cache_rooms(client: AsyncClient):
    rooms_json = {}

    # Hacky way to _really_ sync fully
    client.next_batch = None
    client.loaded_sync_token = None
    await client.sync(60000, full_state = True)

    rooms = client.rooms
    for room_id, room in rooms.items():
        names = [key for key in room.names.keys()]

        source = None
        for name in names:
            if 'bridge bot' in name.lower():
                source = name.split()[0]
                names.remove(name)
                break
        
        if (not source):
            source = room.display_name

        rooms_json[room_id] = {
            'id': room_id,
            'source': source,
            'names': names,
            'display_name': re.sub(r'(.*?)( \(@.*| and \d+ others?)?', '\\1', room.display_name),
            'unread_highlights': room.unread_highlights,
            'unread_notifications': room.unread_notifications,
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
    filtered_rooms = list(filter(lambda r: r['ratio'] >= 70, map(lambda r: assoc_ratio(r, room_name), rooms_json.values())))
    sorted_rooms = sorted(filtered_rooms, key=lambda r: r['ratio'])
    return sorted_rooms[-1]

async def main_dev():
    client = await authenticate_with_matrix()
    rooms = await retrieve_and_cache_rooms(client)
    print(9)

if __name__ == '__main__':
    asyncio.run(main_dev())
