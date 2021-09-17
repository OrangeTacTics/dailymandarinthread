import typing as t
import os

import discord
from discord.ext import commands, tasks


class SyncCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('SyncCog')
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)

        self.loop_incremental_member_update.start()
        #self.loop_full_member_update.start()

    @tasks.loop(seconds=1)
    async def loop_incremental_member_update(self):
        await self.chairmanmao.incremental_member_update()

    @tasks.loop(hours=24)
    async def loop_full_member_update(self):
        guild = client.guilds[0]
        self.chairmanmao.logger.info('Starting full member update')
        await self.chairmanmao.full_member_update(guild)
        self.chairmanmao.logger.info('Full member update complete')
