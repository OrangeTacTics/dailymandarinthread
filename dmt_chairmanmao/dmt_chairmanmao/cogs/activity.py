import asyncio

import discord
from discord.ext import commands, tasks

from dmt_chairmanmao.cogs import ChairmanMaoCog


class ActivityCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("ActivityCog")
        self.activity_queue = set()
        self.activity_loop.start()

        one_day_in_seconds = 86400
        await asyncio.sleep(one_day_in_seconds)
        self.defect_loop.start()

    @tasks.loop(seconds=5)
    async def activity_loop(self):
        user_ids = list(self.activity_queue)
        if len(user_ids) > 0:
            self.logger.info(f"Syncing {len(user_ids)} users: {user_ids}")
            self.activity_queue = set()
            await self.api.alert_activity(user_ids)

    @tasks.loop(minutes=1440)
    async def defect_loop(self):
        constants = self.chairmanmao.constants()
        self.logger.info("Running defector detection loop")
        user_ids = [str(m.id) for m in constants.guild.members]
        await self.api.sync_users(user_ids)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.channel.TextChannel):
            constants = self.chairmanmao.constants()
            if constants.comrade_role in message.author.roles:
                if not message.author.bot:
                    self.activity_queue.add(message.author.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.api.comrade_joined(member.id, member.name + '#' + member.discriminator)
        self.activity_queue.add(member.id)

        constants = self.chairmanmao.constants()
        username = self.chairmanmao.member_to_username(member)
        self.logger.info(f"User joined: {username}. Member ID: {member.id}.")

        embed = discord.Embed(
            title="A Comrade has joined us!",
            description=f"{member.mention} has joined the Daily Mandarin Thread.",
            color=0xFF0000,
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.avatar_url,
        )
        await constants.tiananmen_channel.send(embed=embed)
        if await self.api.is_registered(member.id):
            try:
                await self.api.register(member.id, username)
            except Exception as e:
                self.logger.error(str(e))

        self.logger.info(f"Adding new member to the queue: {member.id}")
        self.activity_queue.add(member.id)

#        if await self.api.is_registered(member.id):
#            self.logger.info(f"A former Comrade rejoined us: {username}. Member ID: {member.id}.")
#
#            embed = discord.Embed(
#                title="A former Comrade has rejoined us!",
#                description=f"{member.mention} has returned to the Daily Mandarin Thread.",
#                color=0xFF0000,
#            )
#
#            embed.set_author(
#                name=member.display_name,
#                icon_url=member.avatar_url,
#            )
#
#            await constants.tiananmen_channel.send(embed=embed)
#
#            embed = discord.Embed(
#                title="Comrade has been jailed!",
#                description=f"{member.mention} has been jailed.",
#                color=0xFF0000,
#            )
#
#            embed.set_author(
#                name=member.display_name,
#                icon_url=member.avatar_url,
#            )
#
#            embed.add_field(
#                name="Reason",
#                value="Defecting from the Daily Mandarin Thread.",
#            )
#            await constants.apologies_channel.send(embed=embed)
#
#        else:
#            await self.api.register(member.id, username)
#
#            self.logger.info(f"A new Comrade has joined us: {username}. Member ID: {member.id}.")
#
#            try:
#                await self.welcome(member)
#            except:
#                self.logger.info(f"Could not send welcome message to {username}. Member ID: {member.id}.")
#
#            embed = discord.Embed(
#                title="A new Comrade has joined us!",
#                description=f"{member.mention} has joined the Daily Mandarin Thread.",
#                color=0xFF0000,
#            )
#
#            embed.set_author(
#                name=member.display_name,
#                icon_url=member.avatar_url,
#            )
#            await constants.tiananmen_channel.send(embed=embed)
#
#        self.chairmanmao.queue_member_update(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        bot_user_id = await self.chairmanmao.bot_user_id()
        await self.api.comrade_defected(member.id)
        await self.api.jail(member.id, bot_user_id, "Defected.")

        username = self.chairmanmao.member_to_username(member)
        self.logger.info(f"User left: {username}. Member ID: {member.id}.")
        constants = self.chairmanmao.constants()

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
