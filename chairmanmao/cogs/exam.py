import typing as t

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile
from chairmanmao.cogs import ChairmanMaoCog


class ExamCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ExamCog')

    @commands.command(name='exam')
    @commands.is_owner()
    async def cmd_exam(self, ctx):
        embed=discord.Embed(
            title="Sample Embed",
            url="https://dailymandarinthread.info",
            description="A based Chinese language learning community.",
            color=0xff0000,
        )
    await ctx.send(embed=embed)
