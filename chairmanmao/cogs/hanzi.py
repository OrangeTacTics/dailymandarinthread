import typing as t

import discord
from discord.ext import commands

from chairmanmao.hanzi import hanzis_in
from chairmanmao.types import Profile


class HanziCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('HanziCog')

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

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()

        if isinstance(message.channel, discord.channel.TextChannel):
            if constants.comrade_role in message.author.roles:
                hanzis = hanzis_in(message.content)
                self.chairmanmao.api.as_comrade(message.author.id).see_hanzis(hanzis)
