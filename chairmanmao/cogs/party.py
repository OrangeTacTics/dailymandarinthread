import typing as t

from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class PartyCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('PartyCog')

    @commands.command(name='stepdown', help="Remove 共产党员 role.")
    @commands.has_role('共产党员')
    async def cmd_stepdown(self, ctx):
        await self.chairmanmao.api.demote(ctx.author.id)
        self.chairmanmao.queue_member_update(ctx.author.id)
        await ctx.send(f'{ctx.author.display_name} has stepped down from the CCP.')

    @commands.command(name='jail')
    @commands.has_role('共产党员')
    async def cmd_jail(self, ctx, member: commands.MemberConverter, *, reason: t.Optional[str] = None):
        await self.chairmanmao.api.jail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        self.chairmanmao.logger.info(f'{ctx.author.display_name} has jailed Comrade {username}. Reason: {repr(reason)}')

        if reason is None:
            display_reason = ''
        else:
            display_reason = f'Reason: {reason}'

        await constants.apologies_channel.send(f'Comrade {username} has been jailed. {display_reason}')
        await self.chairmanmao.api.dishonor(member.id, 25)

    @commands.command(name='unjail')
    @commands.has_role('共产党员')
    async def cmd_unjail(self, ctx, member: commands.MemberConverter):
        await self.chairmanmao.api.unjail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        self.chairmanmao.logger.info(f'{ctx.author.display_name} has unjailed Comrade {username}.')
        await constants.apologies_channel.send(f'Comrade {username} has been unjailed.')

    @commands.command(name='honor', help="Add social credit to a user.")
    @commands.has_role('共产党员')
    async def cmd_honor(self, ctx, member: commands.MemberConverter, credit: int):
        assert credit > 0

        constants = self.chairmanmao.constants()

        if ctx.author != constants.guild.owner:
            if credit > 25:
                await ctx.send('Party members can only honor 25 social credit at a time.')
                return

        target_username = self.chairmanmao.member_to_username(member)
        new_credit = await self.chairmanmao.api.honor(member.id, credit)
        old_credit = new_credit - credit

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{target_username} has had their credit score increased from {old_credit} to {new_credit}.')

    @commands.command(name='dishonor', help="Remove social credit from a user.")
    @commands.has_role('共产党员')
    async def cmd_dishonor(self, ctx, member: commands.MemberConverter, credit: int):
        assert credit > 0

        constants = self.chairmanmao.constants()

        if ctx.author != constants.guild.owner:
            if credit > 25:
                await ctx.send('Party members can only dishonor 25 social credit at a time.')
                return

        target_username = self.chairmanmao.member_to_username(member)
        new_credit = await self.chairmanmao.api.dishonor(member.id, credit)
        old_credit = new_credit + credit

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{target_username} has had their credit score decreased from {old_credit} to {new_credit}.')
