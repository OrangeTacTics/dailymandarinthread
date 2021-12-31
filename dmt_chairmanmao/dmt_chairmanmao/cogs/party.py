import typing as t

import discord
from discord.ext import commands

from dmt_chairmanmao.cogs import ChairmanMaoCog


class PartyCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("PartyCog")

    @commands.command(name="stepdown", help="Remove 共产党员 role.")
    @commands.has_role("共产党员")
    async def cmd_stepdown(self, ctx):
        await self.api.demote(ctx.author.id)
        self.chairmanmao.queue_member_update(ctx.author.id)
        await ctx.send(f"{ctx.author.display_name} has stepped down from the CCP.")

    @commands.command(name="jail")
    @commands.has_role("共产党员")
    async def cmd_jail(self, ctx, member: commands.MemberConverter, *, reason: t.Optional[str] = None):
        await self.api.jail(member.id, ctx.author.id, reason or '')
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        self.logger.info(f"{ctx.author.display_name} has jailed Comrade {username}. Reason: {repr(reason)}")

        embed = discord.Embed(
            title="Comrade has been jailed!",
            description=f"{member.mention} has been jailed.",
            color=0xFF0000,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )

        if reason is not None:
            embed.add_field(
                name="Reason",
                value=reason,
            )

        await constants.apologies_channel.send(embed=embed)
        await self.api.dishonor(member.id, constants.bot_user_id, 25, f"Jailed: {reason}")

    @commands.command(name="unjail")
    @commands.has_role("共产党员")
    async def cmd_unjail(self, ctx, member: commands.MemberConverter):
        await self.api.unjail(member.id, ctx.author.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        self.logger.info(f"{ctx.author.display_name} has unjailed Comrade {username}.")

        embed = discord.Embed(
            title="Comrade has been unjailed!",
            description=f"{member.mention} has been unjailed.",
            color=0xFF0000,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )

        await constants.apologies_channel.send(embed=embed)

    @commands.command(name="honor", help="Add social credit to a user.")
    @commands.has_role("共产党员")
    async def cmd_honor(
        self,
        ctx,
        member: commands.MemberConverter,
        credit: int,
        *,
        reason: t.Optional[str] = None,
    ):
        assert credit > 0

        constants = self.chairmanmao.constants()

        if ctx.author != constants.guild.owner:
            if credit > 25:
                await ctx.send("Party members can only honor 25 social credit at a time.")
                return

        await self.api.honor(member.id, ctx.author.id, credit, reason or '')

        self.chairmanmao.queue_member_update(member.id)

        embed = discord.Embed(
            title="Comrade has been honored!",
            description=f"Comrade {member.mention} has been granted {credit} social credit.",
            color=0x00FF00,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )

        if reason is not None:
            embed.add_field(
                name="Reason",
                value=reason,
                inline=True,
            )

        await ctx.send(embed=embed)

    @commands.command(name="dishonor", help="Remove social credit from a user.")
    @commands.has_role("共产党员")
    async def cmd_dishonor(
        self,
        ctx,
        member: commands.MemberConverter,
        credit: int,
        *,
        reason: t.Optional[str] = None,
    ):
        assert credit > 0

        constants = self.chairmanmao.constants()

        if ctx.author != constants.guild.owner:
            if credit > 25:
                await ctx.send("Party members can only dishonor 25 social credit at a time.")
                return

        await self.api.dishonor(member.id, ctx.author.id, credit, reason or '')

        self.chairmanmao.queue_member_update(member.id)

        embed = discord.Embed(
            title="Comrade has been dishonored!",
            description=f"Comrade {member.mention} has lost {credit} social credit.",
            color=0xFF0000,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )

        if reason is not None:
            embed.add_field(
                name="Reason",
                value=reason,
                inline=True,
            )

        await ctx.send(embed=embed)
