from __future__ import annotations
import typing as t
import logging

import discord
from discord.ext import commands

from dmt_chairmanmao.filemanager import FileManager
from dmt_chairmanmao.api import Api
from dmt_chairmanmao.draw import DrawManager
from dmt_chairmanmao.fourchan import FourChanManager
from dmt_chairmanmao.types import UserId
from dmt_chairmanmao.config import Configuration

from dmt_chairmanmao.discord import DiscordConstants

from dmt_chairmanmao.cogs.sync import SyncCog
from dmt_chairmanmao.cogs.activity import ActivityCog
from dmt_chairmanmao.cogs.socialcredit import SocialCreditCog
from dmt_chairmanmao.cogs.learners import LearnersCog
from dmt_chairmanmao.cogs.draw import DrawCog
from dmt_chairmanmao.cogs.owner import OwnerCog
from dmt_chairmanmao.cogs.comrade import ComradeCog
from dmt_chairmanmao.cogs.party import PartyCog
from dmt_chairmanmao.cogs.voicechat import VoiceChatCog
from dmt_chairmanmao.cogs.fourchan import FourChanCog
from dmt_chairmanmao.cogs.bump import BumpCog
from dmt_chairmanmao.cogs.welcome import WelcomeCog
from dmt_chairmanmao.cogs.exam import ExamCog
from dmt_chairmanmao.cogs.moderation import ModerationCog
from dmt_chairmanmao.cogs.tiananmen import TiananmenCog

# from dmt_chairmanmao.cogs.invites import InvitesCog


################################################################################
# Logging
################################################################################


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
streamformat = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
stream.setFormatter(streamformat)
logger.addHandler(stream)


class ChairmanMao:
    def __init__(self, configuration: Configuration) -> None:
        self.logger = logger
        self.configuration = configuration

        GRAPHQL_ENDPOINT = configuration.GRAPHQL_ENDPOINT
        GRAPHQL_TOKEN = configuration.GRAPHQL_TOKEN

        self.api = Api(GRAPHQL_ENDPOINT, GRAPHQL_TOKEN)

        self.member_update_queue: t.Set[discord.Member] = set()
        self.constants_cache: t.Optional[DiscordConstants] = None

        file_manager = FileManager(configuration)
        self.draw_manager = DrawManager(file_manager)
        self.fourchan_manager = FourChanManager(file_manager)

    async def chairmanmao_user_id(self) -> int:
        return await self.api.get_user_id(self.configuration.BOT_USERNAME)

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

        DISCORD_TOKEN = self.configuration.DISCORD_TOKEN
        client.run(DISCORD_TOKEN)
