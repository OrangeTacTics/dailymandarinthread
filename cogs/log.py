from cogs.lib import DmtEventer
import asyncio
import os
import json
import time
from redis import Redis
from cogs.lib import DmtEventer


redis = Redis()


async def main():
    eventer = DmtEventer()
    async for event in eventer.get_events():
        if event.type == 'MessageCreate':
            payload = event.payload
            if payload['content'].startswith('!log') and payload['edited_timestamp'] is None:
                handle_event(eventer, event)


def handle_event(eventer, event):
    channel_id = event.payload['channel_id']
    content = event.payload['content']
    user_id = event.payload['author']['id']
    username = event.payload['author']['username']
    timestamp = event.payload['timestamp']

    print('handle_message:', username, content)

    assert content.startswith('!log')
    content = content[len('!log'):].strip()

    redis_key = f'logs:{user_id}'

    if content:
        redis.rpush(
            redis_key,
            json.dumps([
                timestamp,
                content,
            ]),
        )

        eventer.create_message(channel_id, 'Log recorded')

    else:
        message_content_lines = [f'Log for {username}']
        for log_record in redis.lrange(redis_key, 0, -1):
            datetime, content = json.loads(log_record)
            datetime = datetime.split('T')[0]
            message_content_lines.append(f'{datetime} {content}')

        eventer.create_message(
            channel_id,
            '\n'.join(message_content_lines),
            suppress_embeds=True,
        )


if __name__ == '__main__':
    asyncio.run(main())
