import typing as t
import os
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks


class ChairmanMaoCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao
        self.logger = chairmanmao.logger

    async def cog_before_invoke(self, ctx: commands.Context):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        now_str = str(now)[:-6]
        author = self.chairmanmao.member_to_username(ctx.author)
        command_name = ctx.command.name
        self.logger.info(f'{author}: {command_name}()')
