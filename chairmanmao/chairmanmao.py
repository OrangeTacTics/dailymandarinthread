from __future__ import annotations
import typing as t
import logging

import discord
from discord.ext import commands

import os

from chairmanmao.filemanager import DoSpacesConfig, FileManager
from chairmanmao.store.mongodb import MongoDbDocumentStore
from chairmanmao.api import Api
from chairmanmao.draw import DrawManager
from chairmanmao.fourchan import FourChanManager
from chairmanmao.types import UserId

from chairmanmao.discord import DiscordConstants

from chairmanmao.cogs.sync import SyncCog
from chairmanmao.cogs.activity import ActivityCog
from chairmanmao.cogs.socialcredit import SocialCreditCog
from chairmanmao.cogs.learners import LearnersCog
from chairmanmao.cogs.draw import DrawCog
from chairmanmao.cogs.owner import OwnerCog
from chairmanmao.cogs.comrade import ComradeCog
from chairmanmao.cogs.party import PartyCog
from chairmanmao.cogs.voicechat import VoiceChatCog
from chairmanmao.cogs.fourchan import FourChanCog
from chairmanmao.cogs.bump import BumpCog
from chairmanmao.cogs.welcome import WelcomeCog
from chairmanmao.cogs.exam import ExamCog
from chairmanmao.cogs.moderation import ModerationCog
from chairmanmao.cogs.tiananmen import TiananmenCog

# from chairmanmao.cogs.invites import InvitesCog


################################################################################
# Logging
################################################################################


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
streamformat = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
stream.setFormatter(streamformat)
logger.addHandler(stream)


class ChairmanMao:
    def __init__(self) -> None:
        self.logger = logger

        GRAPHQL_ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "")
        GRAPHQL_TOKEN = os.getenv("GRAPHQL_TOKEN", "")

        self.api = Api(GRAPHQL_ENDPOINT, GRAPHQL_TOKEN)

        self.member_update_queue: t.Set[discord.Member] = set()
        self.constants_cache: t.Optional[DiscordConstants] = None

        do_spaces_config = DoSpacesConfig.from_environment()
        file_manager = FileManager(do_spaces_config)
        self.draw_manager = DrawManager(file_manager)
        self.fourchan_manager = FourChanManager(file_manager)

    async def chairmanmao_user_id(self) -> int:
        return await self.api.get_user_id(os.environ["BOT_USERNAME"])

    def load_constants(self, guild: discord.Guild) -> None:
        assert self.constants_cache is None
        self.constants_cache = DiscordConstants.load(guild)

    def constants(self) -> DiscordConstants:
        assert self.constants_cache is not None
        return self.constants_cache

    @staticmethod
    def member_to_username(member) -> str:
        return member.name + "#" + member.discriminator

    def queue_member_update(self, user_id: UserId) -> None:
        self.member_update_queue.add(user_id)

    def flush_member_update_queue(self) -> t.List[UserId]:
        user_ids = list(self.member_update_queue)
        self.member_update_queue.clear()
        return user_ids

    def run(self):
        intents = discord.Intents.default()
        intents.members = True
        prefixes = ["$", "!"]
        client = commands.Bot(command_prefix=prefixes, intents=intents)

        client.add_cog(SyncCog(client, self))
        client.add_cog(ActivityCog(client, self))
        client.add_cog(SocialCreditCog(client, self))
        client.add_cog(ComradeCog(client, self))
        client.add_cog(LearnersCog(client, self))
        client.add_cog(OwnerCog(client, self))
        client.add_cog(PartyCog(client, self))
        client.add_cog(DrawCog(client, self))
        client.add_cog(VoiceChatCog(client, self))
        client.add_cog(FourChanCog(client, self))
        client.add_cog(BumpCog(client, self))
        client.add_cog(WelcomeCog(client, self))
        client.add_cog(ExamCog(client, self))
        client.add_cog(ModerationCog(client, self))
        client.add_cog(TiananmenCog(client, self))
        # client.add_cog(InvitesCog(client, self))

        DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        client.run(DISCORD_TOKEN)
