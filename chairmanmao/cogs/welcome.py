import typing as t

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile
from chairmanmao.cogs import ChairmanMaoCog


class WelcomeCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('WelcomeCog')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            profile = self.chairmanmao.api.as_chairman().get_profile(member.id)
            is_new_member = False
        except:
            username = self.chairmanmao.member_to_username(member)
            self.chairmanmao.api.as_chairman().create_profile(member.id, username)
            is_new_member = True

        constants = self.chairmanmao.constants()
        username = self.chairmanmao.member_to_username(member)

        self.chairmanmao.queue_member_update(member.id)

        if is_new_member:
            self.chairmanmao.logger.info(f"New user joined: {username}. Member ID: {member.id}.")
            await self.welcome(member)
            await constants.commentators_channel.send(f'{username} has joined DMT.')
        else:
            self.chairmanmao.logger.info(f"Former user joined: {username}. Member ID: {member.id}.")
            await constants.commentators_channel.send(f'{username} has returned to DMT.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            profile = self.chairmanmao.api.as_chairman().get_profile(member.id)
        except:
            profile = None

        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.logger.info(f"User left: {username}. Member ID: {member.id}.")
        constants = self.chairmanmao.constants()
        await constants.commentators_channel.send(f'{username} has left DMT.')

    async def welcome(self, member) -> None:
        welcome_lines = [
            'Welcome to the Daily Mandarin Thread',
            'https://dailymandarinthread.info',
            '',
            'Our general chat channel is called #🐉网络评论员.',
            '',
            "The numbers in our members' usernames are their social credit score. Be a good citizen, "
            "and you will see your social credit increase.",
            '',
            'You may use the `$learner` command to give yourself the @中文学习者 (Chinese learner) role. '
            'This will give you access to our learning resources and to take tests.',
            '',
            'For more information about the various channels: https://dailymandarinthread.info/discord/channels/',
            'For more information about the various roles: https://dailymandarinthread.info/discord/roles/',
            '',
            'Some good commands to know about:',
            '```',
            '    $draw 猫',
            '        Draws a character',
            '',
            '    $learner',
            '        Grants yourself the @中文学习者 role.',
            '',
            '    $test',
            '        @中文学习者 only. Get the command to take your next test.',
            '',
            '    $leaderboard',
            '        Shows the social credit leaderboard',
            '```',
        ]
        welcome_message = '\n'.join(welcome_lines)

        channel = await member.create_dm()
        await channel.send(welcome_message)

    @commands.command(name='welcomeme')
    async def cmd_welcomeme(self, ctx):
        await self.welcome(ctx.author)
