import discord
from discord.ext import commands, tasks

from chairmanmao.cogs import ChairmanMaoCog


class ActivityCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("ActivityCog")
        self.activity_queue = set()
        self.loop.start()

    @tasks.loop(seconds=5)
    async def loop(self):
        user_ids = list(self.activity_queue)
        if len(user_ids) > 0:
            self.activity_queue = set()
            await self.api.alert_activity(user_ids)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.channel.TextChannel):
            constants = self.chairmanmao.constants()
            if constants.comrade_role in message.author.roles:
                if not message.author.bot:
                    self.activity_queue.add(message.author.id)
