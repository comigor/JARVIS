import asyncio
from nio import AsyncClient, AsyncClientConfig
import json
import re
from fuzzywuzzy import fuzz
import aiofiles

json_fname = 'rooms.json'
CONFIG_FILE = "credentials.json"  # login credentials JSON file
STORE_PATH = "./store/"  # local directory


async def authenticate_with_matrix():
    try:
        client_config = AsyncClientConfig(
            max_limit_exceeded=0,
            max_timeouts=0,
            store_sync_tokens=True,
            encryption_enabled=True,
        )

        # open the file in read-only mode
        async with aiofiles.open(CONFIG_FILE, "r") as f:
            contents = await f.read()
        config = json.loads(contents)
        # Initialize the matrix client based on credentials from file
        client = AsyncClient(
            config["homeserver"],
            config["user_id"],
            device_id=config["device_id"],
            store_path=STORE_PATH,
            config=client_config,
        )

        client.restore_login(
            user_id=config["user_id"],
            device_id=config["device_id"],
            access_token=config["access_token"],
        )
        print("Logged in using stored credentials.")

        return client
    except Exception:
        return None

async def retrieve_and_cache_rooms(client):
    await client.sync(60000)

    rooms = client.rooms
    rooms_json = {}
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
        
        if (room_id == '!jgWE3HRXsPCOXlaCjnPS:beeper.local'):
            print('breakpoint')

        # names = list(filter(lambda x: x.lower() not in ["name_to_filter_1", "name_to_filter_2"], names))

        rooms_json[room_id] = {
            'id': room_id,
            'source': source,
            'names': names,
            'display_name': re.sub(r'(.*?)( and \d+ others?)?', '\\1', room.display_name),
            'unread_highlights': room.unread_highlights,
            'unread_notifications': room.unread_notifications,
        }
        if(names):
            print(f"{names[0]} ({source})  [{len(names)}]")
        else:
            print(f"{room.display_name} ({source}) - No names found")

    print(f"\nFound {len(rooms_json)} rooms! Writing to {json_fname}")
    with open(json_fname, 'w') as f:
        f.write(json.dumps(rooms_json, indent=4))

    print(f"\nUpdated {json_fname}")
    await client.close()

    return rooms_json

def assoc_ratio(room, room_name):
    return {
        **room,
        'ratio': fuzz.ratio(room_name.lower(), room['display_name'].lower()),
    }

def find_room_id_by_name(rooms, room_name: str):
    filtered_rooms = list(map(lambda r: assoc_ratio(r, room_name), rooms.values()))
    sorted_rooms = sorted(filtered_rooms, key=lambda r: r['ratio'])
    return sorted_rooms[-1]

async def main_dev():
    client = await authenticate_with_matrix()
    rooms = await retrieve_and_cache_rooms(client)
    print(9)

if __name__ == '__main__':
    asyncio.run(main_dev())
