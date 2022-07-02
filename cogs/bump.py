import os
import json
from discord.ext import tasks
import discord
import time
from redis import Redis

TWO_HOURS_IN_SECONDS = 2 * 60 * 60


redis = Redis()

redis_seconds, redis_millis = redis.time()
LAST_BUMP = int(str(redis_seconds) + str(redis_millis)[:3]) - TWO_HOURS_IN_SECONDS * 1000

WAITING_FOR_BUMP = False


client = discord.Client()

@client.event
async def on_ready():
    global CHANNEL
    global BUMPER_ROLE

    guild = client.guilds[0]
    CHANNEL = find_channel(guild, '🏯')
    #BUMPER_ROLE = find_role(guild, 'Bumpers')
    BUMPER_ROLE = find_role(guild, '猫')
    print("BUMP COG STARTING")
    loop.start()


@tasks.loop(seconds=1)
async def loop():
    global LAST_BUMP
    global WAITING_FOR_BUMP

    if WAITING_FOR_BUMP:
        timestamp = heard_bump()
        if timestamp is not None:
            LAST_BUMP = timestamp
            WAITING_FOR_BUMP = False

    else:

        redis_seconds, redis_millis = redis.time()
        now = int(str(redis_seconds) + str(redis_millis)[:3])
        if now > LAST_BUMP + TWO_HOURS_IN_SECONDS * 1000:
            #print('BUMP NOW')
            await CHANNEL.send(BUMPER_ROLE.mention + " Please bump the server with /bump")
            WAITING_FOR_BUMP = True


def heard_bump():
    event_batch = redis.xread({'events': LAST_BUMP}, block=1000)
    for stream_name, events in event_batch:
        for event_id, event in events:
            event_id = event_id.decode()
            event_type = event[b'type'].decode()

            if event_type == 'MessageCreate':
                payload = json.loads(event[b'payload'].decode())
                author = payload['author']

                # If is the Disboard bot...
                if author['bot'] and author['id'] == '302050872383242240':
                    first_embed = payload['embeds'][0]
                    if first_embed['description'].startswith('Bump done! :thumbsup:'):
                        return int(event_id.split('-')[0])

    return None


def find_channel(guild: discord.Guild, prefix: str):
    found_channel = None
    for channel in guild.channels:
        if channel.name.startswith(prefix):
            found_channel = channel
            break

    assert found_channel is not None, f"Channel {prefix} does not exist."
    return found_channel


def find_role(guild: discord.Guild, name: str) -> discord.Role:
    role = discord.utils.get(guild.roles, name=name)
    assert role is not None, f"Role {name} does not exist."
    return role


client.run(os.environ['DISCORD_TOKEN'])
