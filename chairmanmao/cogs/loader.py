import typing as t
import os

import discord
from discord.ext import commands, tasks
from chairmanmao.cogs import ChairmanMaoCog


class LoaderCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('Cog')
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)
