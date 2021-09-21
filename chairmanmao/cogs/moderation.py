import typing as t

import discord
from discord.ext import commands

from chairmanmao.cogs import ChairmanMaoCog


class ModerationCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ModerationCog')

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        constants = self.chairmanmao.constants()
        if message.channel.id == constants.apologies_channel.id:
            return

#        async for log in constants.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
#            deleter = log.user
#           log.extra.channel

        warning = f'A message was deleted: {message.author.name} ({message.author.id}): {repr(message.content)}'
        self.chairmanmao.logger.warning(warning)
        await constants.guild.owner.send(warning)
