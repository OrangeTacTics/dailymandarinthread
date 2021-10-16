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
    async def cmd_jail(self, ctx, member: commands.MemberConverter):
        await self.chairmanmao.api.jail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        await constants.commentators_channel.send(f'{ctx.author.display_name} has jailed Comrade {username}.')
        await constants.apologies_channel.send(f'Comrade {username} has been jailed.')

    @commands.command(name='unjail')
    @commands.has_role('共产党员')
    async def cmd_unjail(self, ctx, member: commands.MemberConverter):
        await self.chairmanmao.api.unjail(member.id)
        username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.queue_member_update(member.id)
        constants = self.chairmanmao.constants()
        await constants.commentators_channel.send(f'{ctx.author.display_name} has unjailed Comrade {username}.')
        await constants.apologies_channel.send(f'Comrade {username} has been unjailed.')
