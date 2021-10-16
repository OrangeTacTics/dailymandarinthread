from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class ComradeCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ComradeCog')

    @commands.command(name='name', help='Set your name.')
    @commands.has_role('同志')
    async def cmd_name(self, ctx, name: str):
        member = ctx.author
        username = self.chairmanmao.member_to_username(member)

        try:
            await self.chairmanmao.api.set_name(member.id, name)
        except:  # noqa
#        await ctx.send("Names are 32 character max.")
#        return
            raise

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{username}'s nickname has been changed to {name}")

    @commands.command(name='yuan')
    @commands.has_role('同志')
    async def cmd_yuan(self, ctx):
        yuan = await self.chairmanmao.api.yuan(ctx.author.id)
        username = self.chairmanmao.member_to_username(ctx.author)
        await ctx.send(f"{username} has {yuan} RNB.")

    @commands.command(name='mine', help='Mine a word.')
    @commands.has_role('同志')
    async def cmd_mine(self, ctx, word: str):
        username = self.chairmanmao.member_to_username(ctx.author)
        await self.chairmanmao.api.mine(ctx.author.id, word)

        await ctx.send(f'{username} has mined: {word}')
