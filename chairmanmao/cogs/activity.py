import discord
from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class ActivityCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ActivityCog')

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()

        if isinstance(message.channel, discord.channel.TextChannel):
            if constants.comrade_role in message.author.roles:
                self.chairmanmao.api.alert_activity(message.author.id)
