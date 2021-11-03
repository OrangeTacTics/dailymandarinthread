import typing as t
import subprocess

from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class OwnerCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("OwnersCog")

    @commands.command(name="debug")
    @commands.is_owner()
    async def cmd_debug(self, ctx):
        breakpoint()

    @commands.command(name="promote")
    @commands.is_owner()
    async def cmd_promote(self, ctx, member: commands.MemberConverter):
        await self.api.promote(member.id)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{member.display_name} has been promoted to the CCP.")

    @commands.command(name="demote")
    @commands.is_owner()
    async def cmd_demote(self, ctx, member: commands.MemberConverter):
        await self.api.demote(member.id)
        self.chairmanmao.queue_member_update(member.id)

    @commands.command(name="setname", help="Sets the name of another user.")
    @commands.is_owner()
    async def cmd_setname(self, ctx, member: commands.MemberConverter, name: str):
        target_username = self.chairmanmao.member_to_username(member)

        try:
            await self.api.set_name(member.id, name)
        except:  # noqa
            #        await ctx.send("Names are 32 character max.")
            #        return
            raise

        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s nickname has been changed to {name}")

    @commands.command(name="setlearner")
    @commands.is_owner()
    async def cmd_setlearner(self, ctx, member: commands.MemberConverter, flag: bool = True):
        target_username = self.chairmanmao.member_to_username(member)
        await self.api.set_learner(member.id, flag)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s learner status has been changed to {flag}")

    @commands.command(name="sethsk")
    @commands.is_owner()
    async def cmd_sethsk(self, ctx, member: commands.MemberConverter, hsk_level: t.Optional[int]):
        target_username = self.chairmanmao.member_to_username(member)
        await self.api.set_hsk(member.id, hsk_level)
        self.chairmanmao.queue_member_update(member.id)
        await ctx.send(f"{target_username}'s HSK level has been changed to {hsk_level}")

    @commands.command(name="userid")
    @commands.is_owner()
    async def cmd_userid(self, ctx, member: commands.MemberConverter):
        await ctx.send(f"{member}'s user id is {member.id}")

    @commands.command(name="version")
    @commands.is_owner()
    async def cmd_version(self, ctx):
        proc = subprocess.run("git rev-parse HEAD".split(" "), capture_output=True)
        git_commit_hash = proc.stdout.decode().strip()
        await ctx.send(f"`{git_commit_hash}`")

    @commands.command(name="disableexams")
    @commands.is_owner()
    async def cmd_disableexams(self, ctx):
        await self.api.disable_exams(True)
        await ctx.send("Exams have been disabled")

    @commands.command(name="enableexams")
    @commands.is_owner()
    async def cmd_enableexams(self, ctx):
        await self.api.disable_exams(False)
        await ctx.send("Exams have been enabled")

    @commands.command(name="syncdefectors")
    @commands.is_owner()
    async def cmd_syncdefectors(self, ctx):
        constants = self.chairmanmao.constants()
        user_ids = [str(m.id) for m in constants.guild.members]
        await self.api.sync_users(user_ids)
        await ctx.send("Finished syncing defectors")
