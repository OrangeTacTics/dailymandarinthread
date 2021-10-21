from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class WelcomeCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('WelcomeCog')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        constants = self.chairmanmao.constants()
        username = self.chairmanmao.member_to_username(member)

        if await self.chairmanmao.api.is_registered(member.id):
            self.chairmanmao.logger.info(f"A former Comrade rejoined us: {username}. Member ID: {member.id}.")
            await constants.commentators_channel.send(f'{username} has returned to DMT.')
        else:
            await self.chairmanmao.api.register(member.id, username)
            self.chairmanmao.logger.info(f"A new Comrade has joined us: {username}. Member ID: {member.id}.")
            await self.welcome(member)
            await constants.commentators_channel.send(f'{username} has joined DMT.')

        self.chairmanmao.queue_member_update(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.logger.info(f"User left: {username}. Member ID: {member.id}.")
        constants = self.chairmanmao.constants()
        await self.chairmanmao.api.jail(member.id)
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
            'You may use the `!learner` command to give yourself the @中文学习者 (Chinese learner) role. '
            'This will give you access to our learning resources and to take exams.',
            '',
            'For more information about the various channels: https://dailymandarinthread.info/discord/channels/',
            '',
            'For more information about the various roles: https://dailymandarinthread.info/discord/roles/',
            '',
            'Some good commands to know about:',
            '```',
            '    !name',
            '        Change your nickname.',
            '',
            '    !draw 猫',
            '        Draws a character.',
            '',
            '    !learner',
            '        Grants yourself the @中文学习者 role.',
            '',
            '    !exam',
            '        Test your Chinese abilities. @中文学习者 only.',
            '',
            '    !leaderboard',
            '        Shows the social credit leaderboard.',
            '```',
        ]
        welcome_message = '\n'.join(welcome_lines)

        channel = await member.create_dm()
        await channel.send(welcome_message)

    @commands.command(name='welcomeme')
    async def cmd_welcomeme(self, ctx):
        await self.welcome(ctx.author)

    @commands.is_owner()
    @commands.command(name='register')
    async def cmd_register(self, ctx, member: commands.MemberConverter):
        assert not await self.chairmanmao.api.is_registered(member.id)
        username = self.chairmanmao.member_to_username(member)
        await self.chairmanmao.api.register(member.id, username)
        self.chairmanmao.queue_member_update(member.id)
