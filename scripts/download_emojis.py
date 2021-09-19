import sys
import os

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
    main()
    await client.close()


def main():
    guild = client.guilds[0]
    constants = DiscordConstants.load(guild)
    for emoji in guild.emojis:
        print(emoji.url, emoji.name)
        resp = requests.get(emoji.url)
        resp.raise_for_status()

        with open(f'data/emojis/{emoji.name}.png', 'wb') as outfile:
            outfile.write(resp.content)


if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    client.run(TOKEN)
