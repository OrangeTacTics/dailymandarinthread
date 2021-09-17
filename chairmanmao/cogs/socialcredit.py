from discord.ext import commands
import discord
from chairmanmao.cogs import ChairmanMaoCog


class SocialCreditCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('SocialCreditCog')

    @commands.command(name='socialcredit', help='See your social credit score.')
    @commands.has_role('同志')
    async def cmd_socialcredit(self, ctx, member: commands.MemberConverter = None):
        if member is None:
            member = ctx.author

        username = self.chairmanmao.member_to_username(ctx.author)
        target_username = self.chairmanmao.member_to_username(member)

        credit = self.chairmanmao.api.as_comrade(ctx.author.id).social_credit(member.id)
        await ctx.send(f'{target_username} has a credit score of {credit}.')

    @commands.command(name='leaderboard', help='Show the DMT leaderboard.')
    @commands.has_role('同志')
    @commands.cooldown(1, 5 * 60, commands.BucketType.guild)
    async def cmd_leaderboard(self, ctx, member: commands.MemberConverter = None):
        lines = [
            "The DMT Leaderboard",
            "```",
        ]

        username = self.chairmanmao.member_to_username(ctx.author)
        for entry in self.chairmanmao.api.as_comrade(ctx.author.id).leaderboard():
            line = f'{entry.credit} ... {entry.display_name}'
            lines.append(discord.utils.remove_markdown(line))

        lines.append("```")

        await ctx.send('\n'.join(lines))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        user_to_credit = reaction.message.author
        if user_to_credit != user:
            target_username = self.chairmanmao.member_to_username(user_to_credit)
            credit = self.chairmanmao.api.as_chairman().honor(user_to_credit.id, 1)
            self.chairmanmao.queue_member_update(user_to_credit.id)
            self.chairmanmao.logger.info(f'User reaction added to {user_to_credit}: {credit}')

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        user_to_credit = reaction.message.author
        if user_to_credit != user:
            target_username = self.chairmanmao.member_to_username(user_to_credit)
            credit = self.chairmanmao.api.as_chairman().dishonor(user_to_credit.id, 1)
            self.chairmanmao.queue_member_update(user_to_credit.id)
            self.chairmanmao.logger.info(f'User reaction removed from {user_to_credit}: {credit}')
