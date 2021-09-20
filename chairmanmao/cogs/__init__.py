from discord.ext import commands


class ChairmanMaoCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao
        self.logger = chairmanmao.logger

    async def cog_before_invoke(self, ctx: commands.Context):
        author = self.chairmanmao.member_to_username(ctx.author)
        command_name = ctx.command.name
        self.logger.info(f'{author}: {command_name}()')
