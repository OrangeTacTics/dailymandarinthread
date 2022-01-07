import discord
from discord.ext import commands

from dmt_chairmanmao.cogs import ChairmanMaoCog


class WelcomeCog(ChairmanMaoCog):
    def init(self) -> None:
        with open("data/welcome.md") as infile:
            self.welcome_message = infile.read()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("WelcomeCog")

    async def welcome(self, member) -> None:
        channel = await member.create_dm()
        await channel.send(self.welcome_message)

    @commands.command(name="welcomeme")
    async def cmd_welcomeme(self, ctx):
        await self.welcome(ctx.author)

    @commands.is_owner()
    @commands.command(name="register")
    async def cmd_register(self, ctx, member: commands.MemberConverter):
        assert not await self.api.is_registered(member.id)
        username = self.chairmanmao.member_to_username(member)
        await self.api.register(member.id, username)
        self.chairmanmao.queue_member_update(member.id)
