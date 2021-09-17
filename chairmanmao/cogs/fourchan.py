import typing as t
import os

import discord
from discord.ext import commands, tasks


class FourChanCog(commands.Cog):
    def __init__(self, client, chairmanmao) -> None:
        self.client = client
        self.chairmanmao = chairmanmao

    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('FourChanCog')
        self.loop_dmtthread.start()

    @tasks.loop(seconds=60)
    async def loop_dmtthread(self):
        constants = self.chairmanmao.constants()
        thread = await self.chairmanmao.fourchan_manager.get_dmt_thread()
        if thread is not None:
            if not self.chairmanmao.fourchan_manager.is_url_seen(thread.url):
                logger.info(f'Found DMT thread: {thread.url}')
                self.chairmanmao.fourchan_manager.see_url(thread.url)
                lines = [
                    thread.title,
                    thread.url,
                ]
                await constants.thread_channel.send('\n'.join(lines))

