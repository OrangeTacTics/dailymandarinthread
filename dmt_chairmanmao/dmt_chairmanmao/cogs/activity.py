import asyncio

import discord
from discord.ext import commands, tasks

from dmt_chairmanmao.cogs import ChairmanMaoCog


class ActivityCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("ActivityCog")
        self.activity_queue = set()
        self.activity_loop.start()

        one_day_in_seconds = 86400
        await asyncio.sleep(one_day_in_seconds)
        self.defect_loop.start()

    @tasks.loop(seconds=5)
    async def activity_loop(self):
        user_ids = list(self.activity_queue)
        if len(user_ids) > 0:
            self.activity_queue = set()
            await self.api.alert_activity(user_ids)

    @tasks.loop(minutes=1440)
    async def defect_loop(self):
        constants = self.chairmanmao.constants()
        self.logger.info("Running defector detection loop")
        user_ids = [str(m.id) for m in constants.guild.members]
        await self.api.sync_users(user_ids)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.channel.TextChannel):
            constants = self.chairmanmao.constants()
            if constants.comrade_role in message.author.roles:
                if not message.author.bot:
                    self.activity_queue.add(message.author.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.api.set_defected(member.id, False)
        self.api.activity_queue.add(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.api.set_defected(member.id, True)
