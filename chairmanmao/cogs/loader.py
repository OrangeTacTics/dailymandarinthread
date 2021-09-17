import typing as t
import os

import discord
from discord.ext import commands, tasks


class LoaderCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('Cog')
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)
