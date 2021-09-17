import typing as t

import discord
from discord.ext import commands


class ActivityCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ActivityCog')

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()

        if isinstance(message.channel, discord.channel.TextChannel):
            if constants.comrade_role in message.author.roles:
                self.chairmanmao.api.as_comrade(message.author.id).alert_activity()
