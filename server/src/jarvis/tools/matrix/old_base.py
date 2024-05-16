import asyncio, logging, json, re, aiofiles
from nio import AsyncClient, AsyncClientConfig, RoomKeyRequest, MegolmEvent
from typing import Any
from fuzzywuzzy import fuzz

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

from nio import MatrixRoom

def assoc_ratio(room: MatrixRoom, room_name: str) -> dict[str, Any]:
    return {
        "room": room,
        'ratio': fuzz.ratio(room_name.lower(), room['display_name'].lower()),
    }

def find_room_id_by_name(rooms: dict[str, MatrixRoom], room_name: str):
    filtered_rooms = list(filter(lambda r: r['ratio'] >= 45, map(lambda r: assoc_ratio(r, room_name), rooms_json.values())))
    sorted_rooms = sorted(filtered_rooms, key=lambda r: r['ratio'])
    return sorted_rooms[-1]

async def main_dev():
    client = await authenticate_with_matrix()
    rooms = await retrieve_and_cache_rooms(client)
    print(9)

if __name__ == '__main__':
    asyncio.run(main_dev())
