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
            self.chairmanmao.api.as_comrade(member.id).set_name(name)
        except:  # noqa
#        await ctx.send("Names are 32 character max.")
#        return
            raise

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{username}'s nickname has been changed to {name}")

    @commands.command(name='yuan')
    @commands.has_role('同志')
    async def cmd_yuan(self, ctx):
        yuan = self.chairmanmao.api.as_comrade(ctx.author.id).yuan()
        username = self.chairmanmao.member_to_username(ctx.author)
        await ctx.send(f"{username} has {yuan} RNB.")

    @commands.command(name='mine', help='Mine a word.')
    @commands.has_role('同志')
    async def cmd_mine(self, ctx, word: str):
        username = self.chairmanmao.member_to_username(ctx.author)
        self.chairmanmao.api.as_comrade(ctx.author.id).mine(word)

        await ctx.send(f'{username} has mined: {word}')
