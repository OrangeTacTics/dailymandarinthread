import sys
import os

from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)


@client.event
async def on_ready():
    main()
    await client.close()


def main():
    for member in client.guilds[0].members:
        print(member.display_name)
        print()
        print('   ', 'member.id          = ', member.id)
        print('   ', 'member.joined_at   = ', member.joined_at)
        print('   ', 'roles                ', [role.name for role in member.roles][1:])
        print()


if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    client.run(TOKEN)
