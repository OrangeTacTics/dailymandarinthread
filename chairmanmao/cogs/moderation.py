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
        if message.channel.id == constants.apologies_channel:
            return

        async for log in constants.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
            deleter = log.user
            break

        self.chairmanmao.logger.warning(f'{deleter.name} ({deleter.id}) deleted a message by {message.author.name} ({message.author.id}): {repr(message.content)}')

        if deleter.id == constants.guild.owner.id:
            return

        await constants.guild.owner.send(f'{deleter.name} ({deleter.id}) deleted a message by {message.author.name} ({message.author.id}):\n{repr(message.content)}')
