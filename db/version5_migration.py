from collections import OrderedDict
import sys
import os

from dotenv import load_dotenv
import pymongo

import discord
from discord.ext import commands, tasks

from chairmanmao.profile import get_profile



intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

MONGODB_URL = os.getenv('MONGODB_URL', '')
MONGODB_DB = os.getenv('MONGODB_DB', '')

MONGODB_TEST_URL = os.getenv('MONGODB_TEST_URL', '')
MONGODB_TEST_DB = os.getenv('MONGODB_TEST_DB', '')

src_mongo_client = pymongo.MongoClient(MONGODB_URL)
src_db = src_mongo_client[MONGODB_DB]

dst_mongo_client = pymongo.MongoClient(MONGODB_TEST_URL)
dst_db = dst_mongo_client[MONGODB_TEST_DB]


@client.event
async def on_ready():
    main()
    await client.close()


def member_to_username(member) -> str:
    return member.name + '#' + member.discriminator


SKIP_USERNAMES = ['Patreon#1968']


def main():
    src_col = src_db['Profiles']
    dst_col = dst_db['Profiles']

    dst_col.delete_many({})

    for member in client.guilds[0].members:
        username = member_to_username(member)
        if username in SKIP_USERNAMES:
            continue

        profile = src_col.find_one({'username': username})

        print(member.display_name)
        print()
        print('   ', 'member.id          = ', member.id)
        print('   ', 'member.joined_at   = ', member.joined_at)
        print('   ', 'roles                ', [role.name for role in member.roles][1:])
        print(profile)
        print()

        discord_roles = [role.name for role in member.roles][1:]

        role_map = OrderedDict([
            ('同志', 'Comrade'),
            ('共产党员', 'Party'),
            ('中文学习者', 'Learner'),
        ])

        roles = []
        for discord_name, cm_name in role_map.items():
            if discord_name in discord_roles:
                roles.append(cm_name)

        dst_col.insert_one({
            'user_id': member.id,
            'discord_username': profile['username'],
            'display_name': profile['display_name'],
            'created': profile['created'],
            'last_seen': profile['last_message'],
            'roles': roles,
            'credit': profile['credit'],
            'yuan': profile['yuan'],
            'hanzi': profile['hanzi'],
            'mined_words': profile['mined_words'],
            'schema_version': 5,
        })


if __name__ == '__main__':
    client.run(TOKEN)
