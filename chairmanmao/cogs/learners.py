from __future__ import annotations

import discord
from discord.ext import commands
from chairmanmao.cogs import ChairmanMaoCog


class LearnersCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('LearnersCog')

    @commands.command(name='learner', help='Add or remove 中文学习者 role.')
    @commands.has_role('同志')
    async def cmd_learner(self, ctx, flag: bool = True):
        learner_role = discord.utils.get(ctx.guild.roles, name="中文学习者")

        self.chairmanmao.api.set_learner(ctx.author.id, flag)
        self.chairmanmao.queue_member_update(ctx.author.id)
        if flag:
            await ctx.send(f'{ctx.author.display_name} has been added to {learner_role.name}')
        else:
            await ctx.send(f'{ctx.author.display_name} has been removed from {learner_role.name}')

    @commands.command(name='hsk', help='See your HSK rank.')
    @commands.has_role('同志')
    async def cmd_hsk(self, ctx, member: commands.MemberConverter = None):
        if member is not None:
            target_member = member
        else:
            target_member = ctx.author

        target_username = self.chairmanmao.member_to_username(target_member)
        hsk_level = self.chairmanmao.api.get_hsk(target_member.id)

        if hsk_level is None:
            await ctx.send(f'{target_username} is unranked.')
        else:
            await ctx.send(f'{target_username} has reached HSK {hsk_level}.')
