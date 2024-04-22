import asyncio
import dataclasses
import sys

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


@dataclasses.dataclass
class SiteResult:
    words: set[str]
    links: set[str]


async def get_words_and_links(session: aiohttp.ClientSession, site: str) -> SiteResult:
    async with session.get(site) as answer:
        soup = BeautifulSoup(await answer.text(), "html.parser")
        print(soup.text.split())
        for link in soup.find_all("a"):
            print(link)
        return SiteResult(
            links=
        )


async def main() -> None:
    site = sys.argv[1]
    logger.info(f"Parsing {site!r}...")
    async with aiohttp.ClientSession() as session:
        async with session.get(site) as answer:
            soup = BeautifulSoup(await answer.text(), "html.parser")
            print(soup.text.split())
            for link in soup.find_all("a"):
                print(link)


if __name__ == "__main__":
    asyncio.run(main())
