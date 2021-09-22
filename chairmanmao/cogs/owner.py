import typing as t

from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class OwnerCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('OwnersCog')

    @commands.command(name='debug')
    @commands.is_owner()
    async def cmd_debug(self, ctx):
        breakpoint()

    @commands.command(name='promote')
    @commands.is_owner()
    async def cmd_promote(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.api.as_chairman().promote(member.id)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{ctx.author.display_name} has been promoted to the CCP.')

    @commands.command(name='demote')
    @commands.is_owner()
    async def cmd_demote(self, ctx, member: commands.MemberConverter):
        self.chairmanmao.api.as_chairman().demote(member.id)
        self.chairmanmao.queue_member_update(member.id)

    @commands.command(name='honor', help="Add social credit to a user.")
    @commands.is_owner()
    async def cmd_honor(self, ctx, member: commands.MemberConverter, credit: int):
        assert credit > 0

        target_username = self.chairmanmao.member_to_username(member)
        new_credit = self.chairmanmao.api.as_chairman().honor(member.id, credit)
        old_credit = new_credit - credit

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{target_username} has had their credit score increased from {old_credit} to {new_credit}.')

    @commands.command(name='dishonor', help="Remove social credit from a user.")
    @commands.is_owner()
    async def cmd_dishonor(self, ctx, member: commands.MemberConverter, credit: int):
        assert credit > 0

        target_username = self.chairmanmao.member_to_username(member)
        new_credit = self.chairmanmao.api.as_chairman().dishonor(member.id, credit)
        old_credit = new_credit + credit

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f'{target_username} has had their credit score decreased from {old_credit} to {new_credit}.')

    @commands.command(name='setname', help="Sets the name of another user.")
    @commands.is_owner()
    async def cmd_setname(self, ctx, member: commands.MemberConverter, name: str):
        target_username = self.chairmanmao.member_to_username(member)

        try:
            self.chairmanmao.api.as_chairman().set_name(member.id, name)
        except:  # noqa
#        await ctx.send("Names are 32 character max.")
#        return
            raise

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s nickname has been changed to {name}")

    @commands.command(name='setlearner')
    @commands.is_owner()
    async def cmd_setlearner(self, ctx, member: commands.MemberConverter, flag: bool = True):
        target_username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.api.as_comrade(member.id).set_learner(flag)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s learner status has been changed to {flag}")

    @commands.command(name='sethsk')
    @commands.is_owner()
    async def cmd_sethsk(self, ctx, member: commands.MemberConverter, hsk_level: t.Optional[int]):
        target_username = self.chairmanmao.member_to_username(member)
        self.chairmanmao.api.as_chairman().set_hsk(member.id, hsk_level)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s HSK level has been changed to {hsk_level}")
