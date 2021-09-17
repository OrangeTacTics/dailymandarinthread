from __future__ import annotations
from dataclasses import dataclass
import asyncio
import requests
import typing as t
from datetime import datetime, timezone
from pathlib import Path
import logging
import re
import json

import discord
from discord.ext import commands

import os
import pymongo

from chairmanmao.filemanager import DoSpacesConfig, FileManager
from chairmanmao.api import Api
from chairmanmao.draw import DrawManager
from chairmanmao.fourchan import FourChanManager
from chairmanmao.types import Profile, UserId, Json, Role

from chairmanmao.discord import DiscordConstants

from chairmanmao.cogs.sync import SyncCog
from chairmanmao.cogs.socialcredit import SocialCreditCog
from chairmanmao.cogs.learners import LearnersCog
from chairmanmao.cogs.draw import DrawCog
from chairmanmao.cogs.owner import OwnerCog
from chairmanmao.cogs.comrade import ComradeCog
from chairmanmao.cogs.party import PartyCog
from chairmanmao.cogs.voicechat import VoiceChatCog
from chairmanmao.cogs.invites import InvitesCog
from chairmanmao.cogs.hanzi import HanziCog
from chairmanmao.cogs.fourchan import FourChanCog


################################################################################
# Logging
################################################################################


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream.setFormatter(streamformat)
logger.addHandler(stream)


#@commands.before_invoke
#async def log(ctx):
#    now = datetime.now(timezone.utc).replace(microsecond=0)
#    now_str = str(now)[:-6]
#    author = member_to_username(ctx.author)
#    command_name = ctx.command.name
#    logger.info(f'{author}: {command_name}()')


class ChairmanMao:
    def __init__(self) -> None:
        self.logger = logger

        MONGODB_URL = os.getenv('MONGODB_URL', '')
        MONGODB_DB = os.getenv('MONGODB_DB', '')

        ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
        BOT_USERNAME = os.getenv('BOT_USERNAME', '')

        mongo_client = pymongo.MongoClient(MONGODB_URL)
        db = mongo_client[MONGODB_DB]
        self.api = Api.connect(MONGODB_URL, MONGODB_DB)

        self.member_update_queue: t.Set[discord.Member] = set()
        self.constants_cache: t.Optional[DiscordConstants] = None

        do_spaces_config = DoSpacesConfig.from_environment()
        file_manager = FileManager(do_spaces_config)
        self.draw_manager = DrawManager(file_manager)
        self.fourchan_manager = FourChanManager(file_manager)

    def load_constants(self, guild: discord.Guild) -> None:
        assert self.constants_cache is None
        self.constants_cache = DiscordConstants.load(guild)

    def constants(self) -> DiscordConstants:
        assert self.constants_cache is not None
        return self.constants_cache

    @staticmethod
    def member_to_username(member) -> str:
        return member.name + '#' + member.discriminator

    async def incremental_member_update(self) -> None:
        for user_id in self.flush_member_update_queue():
            profile = self.api.as_chairman().get_profile(user_id)
            did_update = await self.update_member_nick(profile)
            if did_update:
                await asyncio.sleep(0.5)
            did_update = await self.update_member_roles(profile)
            if did_update:
                await asyncio.sleep(0.5)

    async def full_member_update(self) -> None:
        user_ids = self.api.as_chairman().list_users()
        for user_id in user_ids:
            profile = self.api.as_chairman().get_profile(user_id)
            did_update = await self.update_member_nick(profile)
            if did_update:
                await asyncio.sleep(0.5)
            did_update = await self.update_member_roles(profile)
            if did_update:
                await asyncio.sleep(0.5)

    async def update_member_roles(self, profile: Profile) -> bool:
        '''
            Return if roles updated.
        '''
        member = self.profile_to_member(profile)
        if member is None:
            return False

        current_roles = set(member.roles)

        roles_to_add = self.roles_for(profile).difference(current_roles)
        roles_to_remove = self.nonroles_for(profile).intersection(current_roles)

        if not roles_to_add and not roles_to_remove:
            return False

        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)

        added_roles = sorted(r.name for r in roles_to_add)
        removed_roles = sorted(r.name for r in roles_to_remove)
        logger.info(f'Updating roles: {member.nick}: add {added_roles}, remove {removed_roles}')
        return True

    def roles_for(self, profile: Profile) -> t.Set[discord.Role]:
        constants = self.constants()

        comrade_role = constants.comrade_role
        ccp_role     = constants.ccp_role
        jailed_role  = constants.jailed_role
        learner_role = constants.learner_role
        hsk1         = constants.hsk1_role
        hsk2         = constants.hsk2_role
        hsk3         = constants.hsk3_role
        hsk4         = constants.hsk4_role
        hsk5         = constants.hsk5_role
        hsk6         = constants.hsk6_role

        if profile.is_jailed():
            return {jailed_role}
        else:
            roles = {comrade_role}

            if profile.is_party():
                roles.add(ccp_role)

            if profile.is_learner():
                roles.add(learner_role)

            dmt_hsk_role = profile.hsk_role()

            if dmt_hsk_role is not None:
                hsk_discord_role = {
                    Role.Hsk1: hsk1,
                    Role.Hsk2: hsk2,
                    Role.Hsk3: hsk3,
                    Role.Hsk4: hsk4,
                    Role.Hsk5: hsk5,
                    Role.Hsk6: hsk6,
                }[dmt_hsk_role]

                roles.add(hsk_discord_role)

            return roles

    def nonroles_for(self, profile: Profile) -> t.Set[Role]:
        constants = self.constants()

        all_roles = {
            constants.comrade_role,
            constants.ccp_role,
            constants.jailed_role,
            constants.learner_role,
            constants.hsk1_role,
            constants.hsk2_role,
            constants.hsk3_role,
            constants.hsk4_role,
            constants.hsk5_role,
            constants.hsk6_role,
        }
        return all_roles.difference(self.roles_for(profile))

    def queue_member_update(self,user_id: UserId) -> None:
        self.member_update_queue.add(user_id)

    def flush_member_update_queue(self) -> t.List[UserId]:
        user_ids = list(self.member_update_queue)
        self.member_update_queue.clear()
        return user_ids

    async def update_member_nick(self, profile: Profile) -> bool:
        '''
            Return if nick updated.
        '''
        member = self.profile_to_member(profile)
        if member is None:
            return False

        if member.bot:
            return False

        username = self.member_to_username(member)
        constants = self.constants()
        if member.id == constants.guild.owner.id:
            return False

        if profile.is_jailed():
            new_nick = self.add_label_to_nick(profile.display_name, "【劳改】")
        else:
            label = f' [{profile.credit}]'

            hsk_level = profile.hsk_level()
            if hsk_level is not None:
                hsk_label = {
                    1: '➀',
                    2: '➁',
                    3: '➂',
                    4: '➃',
                    5: '➄',
                    6: '➅',
                }
                label += ' HSK' + hsk_label[hsk_level]

            if profile.is_learner():
                label += '✍'

            new_nick = self.add_label_to_nick(profile.display_name, label)

        if new_nick == member.nick:
            return False

        logger.info(f'Rename {member.nick} -> {new_nick}')
        await member.edit(nick=new_nick)
        return True

    def add_label_to_nick(self, display_name: str, label: str) -> str:
        cutoff = 32 - len(label)
        return display_name[:cutoff] + label

    def profile_to_member(self,  profile: Profile) -> t.Optional[discord.Member]:
        constants = self.constants()
        for member in constants.guild.members:
            if member.id == profile.user_id:
                return member
        return None

    def run(self):
        intents = discord.Intents.default()
        intents.members = True
        client = commands.Bot(command_prefix='$', intents=intents)

        client.add_cog(SyncCog(client, self))
        client.add_cog(SocialCreditCog(client, self))
        client.add_cog(ComradeCog(client, self))
        client.add_cog(LearnersCog(client, self))
        client.add_cog(OwnerCog(client, self))
        client.add_cog(PartyCog(client, self))
        client.add_cog(DrawCog(client, self))
        client.add_cog(VoiceChatCog(client, self))
        client.add_cog(HanziCog(client, self))
        client.add_cog(FourChanCog(client, self))
        #client.add_cog(InvitesCog(client, self))

        DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
        client.run(DISCORD_TOKEN)
