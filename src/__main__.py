import asyncio
import dataclasses
import itertools
import sys
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from src.db import Database


def get_domain_name_from_url(url: str) -> str:
    # http://www.example.test/foo/bar -> www.example.test
    netloc = urllib.parse.urlparse(url).netloc
    # -> example.test
    return ".".join(netloc.split(".")[-2:])


@dataclasses.dataclass
class SiteResult:
    words: set[str]
    links: set[str]


async def get_words_and_links(
    session: aiohttp.ClientSession, site: str
) -> SiteResult:
    logger.info(f"Parsing {site!r}...")
    async with session.get(site) as answer:
        soup = BeautifulSoup(await answer.text(), "html.parser")
        return SiteResult(
            words=set(soup.text.split()),
            links=set(
                map(
                    lambda l: urllib.parse.urljoin(site, l.get("href")),
                    soup.find_all("a"),
                )
            ),
        )


async def main() -> None:
    site = sys.argv[1]

    db = Database()
    async with aiohttp.ClientSession() as session:
        root_results = await get_words_and_links(session, site)
        db.add_result(site, root_results)

        link_generator = db.get_links()
        while True:
            links = set()
            for link in link_generator:
                if len(links == 5):
                    break

                if get_domain_name_from_url(site) not in link:
                    logger.warning(f"{link!r} is not valid!")
                    continue

                links.add(link)

            if len(links) == 0:
                break

            results = await asyncio.gather(
                {get_words_and_links(session, link) for link in links},
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                db.add_result(links[i], result)


if __name__ == "__main__":
    asyncio.run(main())
