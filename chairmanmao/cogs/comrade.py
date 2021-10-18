import discord
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
        await ctx.send(f"{username} has {yuan} RMB.")

    @commands.command(name='give')
    @commands.has_role('同志')
    async def cmd_give(self, ctx, to_member: commands.MemberConverter, amount: int):
        await self.chairmanmao.api.transfer(ctx.author.id, to_member.id, amount)
        await ctx.send(f"{ctx.author.mention} has given {amount} RMB to {to_member.mention}")

    @commands.command(name='mine', help='Mine a word.')
    @commands.has_role('同志')
    async def cmd_mine(self, ctx, word: str):
        username = self.chairmanmao.member_to_username(ctx.author)
        await self.chairmanmao.api.mine(ctx.author.id, word)

        await ctx.send(f'{username} has mined: {word}')

    @commands.command(name='definition')
    @commands.has_role('同志')
    async def cmd_definition(self, ctx, word: str):
        definitions = await self.chairmanmao.api.lookup_word(word)

        if len(definitions) == 0:
            await ctx.send('Word not found: ' + word)
        else:
            definition = definitions[0]

            embed = discord.Embed(
                title="Definition",
                color=0xff0000,
            )

            embed.add_field(
                name="Simplified",
                value=definition.simplified,
                inline=True,
            )

            if definition.traditional != definition.simplified:
                embed.add_field(
                    name="Traditional",
                    value=definition.traditional,
                    inline=True,
                )


            embed.add_field(
                name='Pronunciation',
                value=f'{definition.pinyin}\n{definition.zhuyin}',
                inline=False,
            )

            meaning_lines = []
            for i, meaning in enumerate(definition.meanings[:9]):
                num = chr(ord('➀') + i)
                meaning_lines.append(f'{num} {meaning}')

            embed.add_field(
                name='Meaning',
                value='\n'.join(meaning_lines),
                inline=False,
            )

            await ctx.send(embed=embed)
