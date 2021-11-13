from __future__ import annotations

import discord
from discord.ext import commands
from dmt_chairmanmao.cogs import ChairmanMaoCog
from pathlib import Path
import json


class LearnersCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("LearnersCog")

    @commands.command(name="learner", help="Add or remove 中文学习者 role.")
    @commands.has_role("同志")
    async def cmd_learner(self, ctx, flag: bool = True):
        learner_role = discord.utils.get(ctx.guild.roles, name="中文学习者")

        await self.api.set_learner(ctx.author.id, flag)
        self.chairmanmao.queue_member_update(ctx.author.id)
        if flag:
            await ctx.send(f"{ctx.author.display_name} has been added to {learner_role.name}")
        else:
            await ctx.send(f"{ctx.author.display_name} has been removed from {learner_role.name}")

    @commands.command(name="hsk", help="See your HSK rank.")
    @commands.has_role("同志")
    async def cmd_hsk(self, ctx, member: commands.MemberConverter = None):
        if member is not None:
            target_member = member
        else:
            target_member = ctx.author

        target_username = self.chairmanmao.member_to_username(target_member)
        hsk_level = await self.api.get_hsk(target_member.id)

        if hsk_level is None:
            await ctx.send(f"{target_username} is unranked.")
        else:
            await ctx.send(f"{target_username} has reached HSK {hsk_level}.")

    @commands.command(name="readers", help="List how many words you know in various readers.")
    @commands.has_role("同志")
    async def cmd_readers(self, ctx):
        mined_words = set(await self.api.get_mined(ctx.author.id))

        reader_words_dir = Path("data/reader_words")
        for reader_words_filepath in reader_words_dir.iterdir():
            with open(reader_words_filepath) as infile:
                json_data = json.load(infile)
                title = json_data["title"]
                words = json_data["words"]

            unknown_words = set(words).difference(mined_words)

            await ctx.channel.send(f"{title}: {len(unknown_words)} unmined words")
