import typing as t
import asyncio
import os
import json
from discord.ext import tasks
import discord
import time
from redis import Redis
from dataclasses import dataclass


@dataclass
class Event:
    id: str
    type: str
    payload: t.Any

    def timestamp(self) -> int:
        return int(self.id.split('-')[0])


class Emoji:
    def to_dict(self) -> dict:
        ...


class UnicodeEmoji(Emoji):
    def __init__(self, emoji: str) -> None:
        self.emoji = emoji

    def to_dict(self) -> dict:
        return {
            "type": "Unicode",
            "emoji": self.emoji,
        }


class CustomEmoji(Emoji):
    def __init__(self, id: int) -> None:
        self.id = id

    def to_dict(self) -> dict:
        return {
            "type": "Unicode",
            "id": self.id,
        }


class DmtEventer:
    def __init__(self):
        self.redis = Redis()
        self.last_event = '$'

    async def get_events(self):
        while True:
            event_batch = self.redis.xread({'events': self.last_event}, block=1000)
            for stream_name, events in event_batch:
                for event_id, event in events:
                    event_id = event_id.decode()
                    event_type = event[b'type'].decode()
                    event_payload = json.loads(event[b'payload'].decode())

                    self.last_event = event_id

                    yield Event(
                        id=event_id,
                        type=event_type,
                        payload=event_payload,
                    )

            await asyncio.sleep(0)

    def create_message(
        self,
        channel_id,
        content,
        reply = None,
        suppress_embeds=False,
    ):
        command = {
            'type': 'CreateMessage',
            'channel_id': int(channel_id),
            'content': content,
            'reply': int(reply) if reply else None,
            'suppress_embeds': suppress_embeds,
        }
        self.redis.rpush('commands', json.dumps(command))

    def delete_message(
        self,
        channel_id,
        message_id,
    ):
        command = {
            'type': 'DeleteMessage',
            'channel_id': int(channel_id),
            'message_id': int(message_id),
        }
        self.redis.rpush('commands', json.dumps(command))

    async def create_reaction(self,
        channel_id,
        message_id,
        emoji,
    ):
        assert isinstance(emoji, Emoji), 'emoji must be type Emoji'
        command = {
            'type': 'CreateReaction',
            'channel_id': int(channel_id),
            'message_id': int(message_id),
            'emoji': emoji.to_dict(),
        }
        self.redis.rpush('commands', json.dumps(command))
