import typing as t
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks

from dmt_chairmanmao.cogs import ChairmanMaoCog


class TiananmenCog(ChairmanMaoCog):
    def init(self) -> None:
        self.young_members: t.Dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("TiananmenCog")
        self.loop.start()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        now = datetime.now(timezone.utc)
        self.young_members[member.id] = now

    @tasks.loop(minutes=15)
    async def loop(self):
        now = datetime.now(timezone.utc)
        for member_id, joined in self.young_members.items():
            if now - joined >= timedelta(hours=24):
                self.logger.info(f"Removing new member {member_id} from young users list.")

        self.young_members = {
            member_id: joined for (member_id, joined) in self.young_members.items() if now - joined < timedelta(hours=2)
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()

        if (
            isinstance(message.channel, discord.channel.TextChannel)
            and message.author.id in self.young_members
            and message.channel != constants.apologies_channel
        ):
            if is_infraction(message):
                await self.api.jail(message.author.id)
                self.chairmanmao.queue_member_update(message.author.id)
                self.logger.info("Jailed new user for infraction")


def is_infraction(message: discord.Message) -> bool:
    content = message.content.lower()
    return "tiananmen" in content or "taiwan" in content
