import typing as t

import discord
from discord.ext import commands

from chairmanmao.types import Profile


class PartyCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('PartyCog')

    @commands.command(name='stepdown', help="Remove 共产党员 role.")
    @commands.has_role('共产党员')
    async def  cmd_stepdown(self, ctx):
        self.chairmanmao.api.as_party(ctx.author.id).stepdown()
        self.chairmanmao.queue_member_update(ctx.author.id)
        await ctx.send(f'{ctx.author.display_name} has stepped down from the CCP.')

    @commands.command(name='recognize', help="Remove 共产党员 role.")
    @commands.has_role('共产党员')
    async def cmd_recognize(self, ctx, member: commands.MemberConverter):
        message = ctx.message
        comrade_role = discord.utils.get(message.channel.guild.roles, name='同志')
        username = self.chairmanmao.member_to_username(member)
        assert comrade_role not in member.roles, 'Member is already a 同志.'

        self.chairmanmao.api.as_party(ctx.author.id).recognize(member.id, username)

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{ctx.author.display_name} has recognized Comrade {username}.')

    @commands.command(name='jail')
    @commands.has_role('共产党员')
    async def cmd_jail(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.api.as_party(ctx.author.id).jail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{ctx.author.display_name} has jailed Comrade {username}.')

    @commands.command(name='unjail')
    @commands.has_role('共产党员')
    async def cmd_unjail(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.api.as_party(ctx.author.id).unjail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{ctx.author.display_name} has unjailed Comrade {username}.')
