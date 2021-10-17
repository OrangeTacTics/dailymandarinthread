from datetime import datetime, timezone

from discord.ext import commands, tasks

from chairmanmao.cogs import ChairmanMaoCog


TWO_HOURS_IN_SECONDS = 2 * 60 * 60


class BumpCog(ChairmanMaoCog):
    def __init__(self, client, chairmanmao) -> None:
        super().__init__(client, chairmanmao)
        self.last_bump = datetime.now(timezone.utc)

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('BumpCog')
        self.loop_bump_timer.start()

    def seconds_since_last_bump(self) -> int:
        now = datetime.now(timezone.utc)
        duration_since_last_bump = now - self.last_bump
        return int(duration_since_last_bump.total_seconds())

    @tasks.loop(minutes=1)
    async def loop_bump_timer(self):
        if self.last_bump is not None:
            if self.seconds_since_last_bump() > TWO_HOURS_IN_SECONDS:
                self.last_bump = None
                channel = self.chairmanmao.constants().bump_channel

                bumpers = self.chairmanmao.constants().bumpers_role.mention
                await channel.send(f'{bumpers} Please bump the server with `!d bump`')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.seconds_since_last_bump() < TWO_HOURS_IN_SECONDS:
            return

        constants = self.chairmanmao.constants()
        if message.channel == constants.bump_channel:
            if message.content.strip() == '!d bump':
                self.last_bump = datetime.now(timezone.utc)
                await self.chairmanmao.api.transfer(
                    await self.chairmanmao.chairmanmao_user_id(),
                    message.author.id,
                    1,
                )
                self.chairmanmao.logger.info('Server has been bumped')
