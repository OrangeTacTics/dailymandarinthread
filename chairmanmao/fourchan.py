from __future__ import annotations
import typing as t
from io import BytesIO
from dataclasses import dataclass
import asyncio
import json
import httpx

from discord.ext import commands, tasks

from chairmanmao.filemanager import FileManager


if t.TYPE_CHECKING:
    from chairmanmao.types import Json


@dataclass
class DmtThread:
    title: str
    url: str
    json: t.Any


class FourChanManager:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager
        self.urls_seen: t.Optional[t.Set[str]] = None

    async def _get_int_catalog(self) -> Json:
        async with httpx.AsyncClient() as client:
            url = 'https://a.4cdn.org/int/catalog.json'
            response = await client.get(url)
            return response.json()

    def _thread_by_title_fuzzy(self, catalog: Json, thread_title: str) -> Json:
        for page in catalog:
            threads = page['threads']
            for thread in threads:
                if thread_title in thread.get("sub", ""):
                    return thread

        return None

    def _url_for_thread(self, thread: Json) -> str:
        return 'https://boards.4channel.org/int/thread/' + str(thread["no"])

    def _title_for_thread(self, thread: Json) -> str:
        return thread["sub"]

    def _is_url_seen(self, url: str) -> bool:
        if self.urls_seen is None:
            print('loading urls from database... 1')
            infile = self.file_manager.download('fourchan/seen_urls.json')
            self.urls_seen = set(json.load(infile))

        return url in self.urls_seen

    def see_url(self, url: str) -> None:
        if self.urls_seen is None:
            print('loading urls from database... 2')
            infile = self.file_manager.download('fourchan/seen_urls.json')
            self.urls_seen = set(json.load(infile))

        self.urls_seen.add(url)

        buf = BytesIO(json.dumps(sorted(self.urls_seen)).encode('utf-8'))
        self.file_manager.upload('fourchan/seen_urls.json', buf)


    async def get_dmt_thread(self) -> t.Optional[DmtThread]:
        catalog = await self._get_int_catalog()
        thread = self._thread_by_title_fuzzy(catalog, 'Daily Mandarin Thread')
        if thread:
            title = self._title_for_thread(thread)
            url = self._url_for_thread(thread)
            self.see_url(url)
            return DmtThread(
                title=title,
                url=url,
                json=thread,
            )
        else:
            return None


################################################################################
# 4chan Threads
################################################################################

def thread_channel():
    guild = client.guilds[0]
    assert guild.name == 'Daily Mandarin Thread'

    for channel in guild.channels:
        if channel.name.startswith('🧵'):
            return channel

    raise Exception()


@tasks.loop(seconds=60)
async def loop_dmtthread():
    thread = await fourchan_manager.get_dmt_thread()
    if thread is not None:
        if not fourchan_manager.is_url_seen(thread.url):
            logger.info(f'Found DMT thread: {thread.url}')
            fourchan_manager.see_url(thread.url)
            channel = thread_channel()
            lines = [
                thread.title,
                thread.url,
            ]
            await channel.send('\n'.join(lines))
