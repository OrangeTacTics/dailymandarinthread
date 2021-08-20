import typing as t
from dataclasses import dataclass
import asyncio
import json
import httpx

async def get_int_catalog():
    async with httpx.AsyncClient() as client:
        url = 'https://a.4cdn.org/int/catalog.json'
        response = await client.get(url)
        return response.json()


def thread_by_title_fuzzy(catalog, thread_title):
    for page in catalog:
        threads = page['threads']
        for thread in threads:
            if thread_title in thread.get("sub", ""):
                return thread

    return None


def url_for_thread(thread):
    return 'https://boards.4channel.org/int/thread/' + str(thread["no"])


def title_for_thread(thread):
    return thread["sub"]


@dataclass
class DmtThread:
    title: str
    url: str
    json: t.Any


URLS_SEEN: t.Set[str] = t.cast(t.Set[str], None)


def is_url_seen(url):
    global URLS_SEEN
    if URLS_SEEN is None:
        print('loading urls from database... 1')
        with open('db/fourchan.json') as infile:
            URLS_SEEN = set(json.load(infile))

    return url in URLS_SEEN


def see_url(url):
    global URLS_SEEN
    if URLS_SEEN is None:
        print('loading urls from database... 2')
        with open('db/fourchan.json') as infile:
            URLS_SEEN = set(json.load(infile))

    URLS_SEEN.add(url)
    with open('db/fourchan.json', 'w') as outfile:
        json.dump(list(URLS_SEEN), outfile)


async def get_dmt_thread() -> t.Optional[DmtThread]:
    catalog = await get_int_catalog()
    thread = thread_by_title_fuzzy(catalog, 'Daily Mandarin Thread')
    if thread:
        title = title_for_thread(thread)
        url = url_for_thread(thread)
        return DmtThread(
            title=title,
            url=url,
            json=thread,
        )
    else:
        return None


async def main():
    print(await get_dmt_url())


if __name__ == "__main__":
    asyncio.run(main())
