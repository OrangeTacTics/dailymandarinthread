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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        constants = self.chairmanmao.constants()
        username = self.chairmanmao.member_to_username(member)

        if await self.api.is_registered(member.id):
            self.logger.info(f"A former Comrade rejoined us: {username}. Member ID: {member.id}.")

            embed = discord.Embed(
                title="A former Comrade has rejoined us!",
                description=f"{member.mention} has returned to the Daily Mandarin Thread.",
                color=0xFF0000,
            )

            embed.set_author(
                name=member.display_name,
                icon_url=member.avatar_url,
            )

            await constants.tiananmen_channel.send(embed=embed)

            embed = discord.Embed(
                title="Comrade has been jailed!",
                description=f"{member.mention} has been jailed.",
                color=0xFF0000,
            )

            embed.set_author(
                name=member.display_name,
                icon_url=member.avatar_url,
            )

            embed.add_field(
                name="Reason",
                value="Defecting from the Daily Mandarin Thread.",
            )
            await constants.apologies_channel.send(embed=embed)

        else:
            await self.api.register(member.id, username)

            self.logger.info(f"A new Comrade has joined us: {username}. Member ID: {member.id}.")

            try:
                await self.welcome(member)
            except:
                self.logger.info(f"Could not send welcome message to {username}. Member ID: {member.id}.")

            embed = discord.Embed(
                title="A new Comrade has joined us!",
                description=f"{member.mention} has joined the Daily Mandarin Thread.",
                color=0xFF0000,
            )

            embed.set_author(
                name=member.display_name,
                icon_url=member.avatar_url,
            )
            await constants.tiananmen_channel.send(embed=embed)

        self.chairmanmao.queue_member_update(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        username = self.chairmanmao.member_to_username(member)
        self.logger.info(f"User left: {username}. Member ID: {member.id}.")
        constants = self.chairmanmao.constants()
        await self.api.jail(member.id)

        embed = discord.Embed(
            title="A Comrade has defected!",
            description=f"{member.mention} has defected from the Daily Mandarin Thread.",
            color=0xFF0000,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )

        await constants.tiananmen_channel.send(embed=embed)

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
