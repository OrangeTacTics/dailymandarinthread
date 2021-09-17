import typing as t
import os

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile
from chairmanmao.hanzi import is_hanzi, hanzis_in


class SyncCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('SyncCog')
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)

        # await init_invites()
        self.chairmanmao.logger.info('Ready.')

        self.loop_incremental_member_update.start()
        #self.loop_full_member_update.start()
        # loop_dmtthread.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()

        if isinstance(message.channel, discord.channel.TextChannel):
            if constants.comrade_role in message.author.roles:
                self.chairmanmao.api.as_comrade(message.author.id).alert_activity()

                hanzis = hanzis_in(message.content)
                self.chairmanmao.api.as_comrade(message.author.id).see_hanzis(hanzis)

    @tasks.loop(seconds=1)
    async def loop_incremental_member_update(self):
        await self.chairmanmao.incremental_member_update()

    @tasks.loop(hours=24)
    async def loop_full_member_update(self):
        guild = client.guilds[0]
        self.chairmanmao.logger.info('Starting full member update')
        await self.chairmanmao.full_member_update(guild)
        self.chairmanmao.logger.info('Full member update complete')

