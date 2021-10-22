from __future__ import annotations
import typing as t
from io import BytesIO
from dataclasses import dataclass
import json
import httpx

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
            url = "https://a.4cdn.org/int/catalog.json"
            response = await client.get(url)
            return response.json()

    def _thread_by_title_fuzzy(self, catalog: Json, thread_title: str) -> Json:
        for page in catalog:
            threads = page["threads"]
            for thread in threads:
                if thread_title in thread.get("sub", ""):
                    return thread

        return None

    def _url_for_thread(self, thread: Json) -> str:
        return "https://boards.4channel.org/int/thread/" + str(thread["no"])

    def _title_for_thread(self, thread: Json) -> str:
        return thread["sub"]

    def is_url_seen(self, url: str) -> bool:
        if self.urls_seen is None:
            infile = self.file_manager.download("fourchan/seen_urls.json")
            self.urls_seen = set(json.load(infile))

        return url in self.urls_seen

    def see_url(self, url: str) -> None:
        if self.urls_seen is None:
            infile = self.file_manager.download("fourchan/seen_urls.json")
            self.urls_seen = set(json.load(infile))

        self.urls_seen.add(url)

        buf = BytesIO(json.dumps(sorted(self.urls_seen)).encode("utf-8"))
        self.file_manager.upload("fourchan/seen_urls.json", buf)

    async def get_dmt_thread(self) -> t.Optional[DmtThread]:
        catalog = await self._get_int_catalog()
        thread = self._thread_by_title_fuzzy(catalog, "Daily Mandarin Thread")
        if thread:
            title = self._title_for_thread(thread)
            url = self._url_for_thread(thread)
            return DmtThread(
                title=title,
                url=url,
                json=thread,
            )
        else:
            return None
