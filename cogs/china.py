import asyncio
import random
from cogs.lib import DmtEventer, UnicodeEmoji
import json
import time
from redis import Redis

reset_window = 60 * 60 # 60 minutes

redis = Redis()
last_timestamp, _microseconds = redis.time()
last_timestamp -= reset_window



def get_redis_timestamp():
    redis_seconds, redis_millis = redis.time()
    return int(str(redis_seconds) + str(redis_millis)[:3])


def get_create_message_events():
    last_timestamp = get_redis_timestamp()
    while True:
        event_batch = redis.xread({'events': last_timestamp}, block=1000)
        for stream_name, events in event_batch:
            for event_id, event in events:
                event_id = event_id.decode()
                last_timestamp = event_id.split('-')[0]
                event_type = event[b'type'].decode()

                if event_type == 'MessageCreate':
                    payload = json.loads(event[b'payload'].decode())
                    yield payload


def is_china(event):
    if event.type == 'MessageCreate':
        lower_content = event.payload['content'].lower()
        return 'china' in lower_content or 'chinese' in lower_content
    else:
        return False


async def main():
    global last_timestamp
    eventer = DmtEventer()
    async for event in eventer.get_events():
        if is_china(event):
            print(event.payload['author']['id'], event.payload['content'])

            next_timestamp, _microseconds = redis.time()
            time_elapsed = next_timestamp - last_timestamp
            last_timestamp = next_timestamp

            probability = min(time_elapsed / reset_window, 1.0)

            if random.random() < probability:
                print(f'{probability:.2f}%, WIN')
                emoji = UnicodeEmoji("🇨🇳")
                channel_id = event.payload['channel_id']
                message_id = event.payload['id']
                await eventer.create_reaction(channel_id, message_id, emoji)
            else:
                print(f'{probability:.2f}%, LOSS')


if __name__ == "__main__":
    asyncio.run(main())
