import sys
import os
from pathlib import Path
import asyncio

import requests

from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks

from chairmanmao.discord import DiscordConstants


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)


@client.event
async def on_ready():
    await main()
    await client.close()


#async def delete_all_emojis(guild):
#    for emoji in guild.emojis:
#        print(emoji.name)
#        print('    deleting...')
#        await emoji.delete()
#        await asyncio.sleep(0.25)
#        print('    complete')

async def create_emojis(guild):
    emojis_dir = Path('data/emojis')
    for emoji_path in emojis_dir.iterdir():
        name = emoji_path.name[:-4]
        print(name)
        emoji = discord.utils.get(guild.emojis, name=name)
        if emoji is not None:
            print('    already exists...')
        else:
            with open(emoji_path, "rb") as infile:
                image = infile.read()
            print('    creating emoji...')
            await guild.create_custom_emoji(name=name, image=image)
            await asyncio.sleep(1)
            print('    completed')


def channel_exists(guild: discord.Guild, prefix: str) -> bool:
    found_channel = None
    for channel in guild.channels:
        if channel.name.startswith(prefix):
            return True

    return False

async def create_channels(guild):
    category = None
    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            category = channel
            break

    channel_names = [
        "📰",
        "🈲",
        "🧵",
        "🐉",
        "✍",
        "🏫",
        "🏯",
        "⛔",
    ]

    for channel_name in channel_names:
        if not channel_exists(guild, channel_name):
            print('Creating channel:', channel_name)
            await category.create_text_channel(name=channel_name)
            await asyncio.sleep(1)


async def create_roles(guild):
    role_names = [
        '同志',
        "共产党员",
        "劳改",
        "中文学习者",
        "HSK1",
        "HSK2",
        "HSK3",
        "HSK4",
        "HSK5",
        "HSK6",
        "Bumpers",
    ]

    for role_name in role_names:
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            print('Creating', role_name)
            await guild.create_role(name=role_name)
            await asyncio.sleep(1)


async def main():
    guild = client.guilds[0]
    assert 'DEV' in guild.name
    print('Setting up:', guild.name)
#    await delete_all_emojis(guild)
    await create_emojis(guild)
    await create_channels(guild)
    await create_roles(guild)

    constants = DiscordConstants.load(guild)
    await constants.commentators_channel.send('DONE')


if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    client.run(TOKEN)
