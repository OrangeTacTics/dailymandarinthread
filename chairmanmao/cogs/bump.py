import typing as t

from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

TWO_HOURS_IN_SECONDS = 2 * 60 * 60


class BumpCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao
        self.last_bump = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('BumpCog')
        self.last_bump = datetime.now(timezone.utc)
        self.loop_bump_timer.start()

    @tasks.loop(minutes=1)
    async def loop_bump_timer(self):
        if self.last_bump is not None:
            now = datetime.now(timezone.utc)
            duration_since_last_bump = now - self.last_bump
            if duration_since_last_bump.total_seconds() > TWO_HOURS_IN_SECONDS:
                self.last_bump = None
                channel = self.chairmanmao.constants().tiananmen_channel

                bumpers = self.chairmanmao.constants().bumpers_role.mention
                await channel.send(f'{bumpers} Please bump the server with `!d bump`')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        constants = self.chairmanmao.constants()
        if message.channel == constants.tiananmen_channel:
            if message.content.strip() == '!d bump':
                self.last_bump = datetime.now(timezone.utc)
                self.chairmanmao.logger.info('Server has been bumped')
