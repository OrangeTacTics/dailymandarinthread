from datetime import datetime, timezone, timedelta

from discord.ext import commands

from dmt_chairmanmao.cogs import ChairmanMaoCog


class ModerationCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("ModerationCog")
        self.last_ping = datetime.now(timezone.utc) - timedelta(hours=24)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        constants = self.chairmanmao.constants()
        if message.channel.id == constants.apologies_channel.id:
            return

        #        async for log in constants.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
        #            deleter = log.user
        #           log.extra.channel

        warning = f"A message was deleted: {message.author.name} ({message.author.id}): {repr(message.content)}"
        self.logger.warning(warning)

        now = datetime.now(timezone.utc)
        minutes_since_last_ping = (now - self.last_ping).total_seconds() // 60

        if minutes_since_last_ping > 30:
            self.last_ping = now
            await constants.guild.owner.send(warning)
