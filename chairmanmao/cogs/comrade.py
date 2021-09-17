import typing as t

import discord
from discord.ext import commands

from chairmanmao.types import Profile


class ComradeCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ComradeCog')

    @commands.command(name='name', help='Set your name.')
    @commands.has_role('同志')
    async def cmd_name(self, ctx, name: str):
        member = ctx.author
        username = self.chairmanmao.member_to_username(member)

        try:
            self.chairmanmao.api.as_comrade(member.id).set_name(name)
        except:
#        await ctx.send("Names are 32 character max.")
#        return
            raise

        profile = self.chairmanmao.api.as_chairman().get_profile(member.id)
        assert profile is not None

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{username}'s nickname has been changed to {name}")

    @commands.command(name='hanzi', help='Show the count and list of all hanzi a user has taken.')
    @commands.has_role('同志')
    async def cmd_hanzi(self, ctx, member: commands.MemberConverter = None):
        if member is None:
            member = ctx.author

        username = self.chairmanmao.member_to_username(ctx.author)
        target_username = self.chairmanmao.member_to_username(member)

        hanzi = self.chairmanmao.api.as_comrade(ctx.author.id).get_hanzis(member.id)
        hanzi_str = ' '.join(hanzi)
        num_hanzi = len(hanzi)
        await ctx.send(f'{target_username} has {num_hanzi} hanzi: {hanzi_str}')


    @commands.command(name='yuan')
    @commands.has_role('同志')
    async def cmd_yuan(self, ctx):
        yuan = self.chairmanmao.api.as_comrade(ctx.author.id).yuan()
        username = self.chairmanmao.member_to_username(ctx.author)
        await ctx.send(f"{username} has {yuan} RNB.")

    @commands.command(name='leaderboard', help='Show the DMT leaderboard.')
    @commands.has_role('同志')
    @commands.cooldown(1, 5 * 60, commands.BucketType.guild)
    async def cmd_leaderboard(self, ctx, member: commands.MemberConverter = None):
        lines = [
            "The DMT Leaderboard",
            "```",
        ]

        username = self.chairmanmao.member_to_username(ctx.author)
        for entry in self.chairmanmao.api.as_comrade(ctx.author.id).leaderboard():
            line = f'{entry.credit} ... {entry.display_name}'
            lines.append(discord.utils.remove_markdown(line))

        lines.append("```")

        await ctx.send('\n'.join(lines))


    @commands.command(name='mine', help='Mine a word.')
    @commands.has_role('同志')
    async def cmd_mine(self, ctx, word: str):
        username = self.chairmanmao.member_to_username(ctx.author)
        self.chairmanmao.api.as_comrade(ctx.author.id).mine(word)

        await ctx.send(f'{username} has mined: {word}')
