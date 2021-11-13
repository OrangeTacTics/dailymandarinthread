from discord.ext import commands
from dmt_chairmanmao.cogs import ChairmanMaoCog


class LoaderCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Cog")
        guild = self.client.guilds[0]
        self.chairmanmao.load_constants(guild)
