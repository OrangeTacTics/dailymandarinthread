import typing as t

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile


class WelcomeCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('WelcomeCog')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            profile = self.chairmanmao.api.as_chairman().get_profile(member.id)
        except:
            profile = None

        if profile is None:
            username = self.chairmanmao.member_to_username(member)
            self.chairmanmao.logger.info(f"New user joined: {username}. Member ID: {member.id}.")
            self.welcome(member)
        else:
            username = self.chairmanmao.member_to_username(member)
            self.chairmanmao.logger.info(f"Former user joined: {username}. Member ID: {member.id}.")

    async def welcome(self, member) -> None:
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.logger.info(f"New user joined: {username}. Member ID: {member.id}.")

        welcome_lines = [
            'Welcome to the Daily Mandarin Thread',
            'https://dailymandarinthread.info',
        ]
        welcome_message = '\n'.join(welcome_lines)

        channel = await member.create_dm()
        await channel.send(welcome_message)

    @commands.command(name='welcomeme')
    @commands.has_role("共产党员")
    @commands.is_owner()
    async def cmd_welcomeme(self, ctx):
        await self.welcome(ctx.author)
