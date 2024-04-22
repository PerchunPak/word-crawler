import asyncio
import dataclasses
import itertools
import sys
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from src.db import Database


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
        logger.success("Parsed root link! Starting to parse children...")

        db.add_result(site, root_results)

        link_generator = db.get_links(root_link=site)
        while True:
            links = set()
            for link in link_generator:
                if len(links) == 5:
                    break
                links.add(link)

            if len(links) == 0:
                logger.success("Done!")
                break

            results = await asyncio.gather(
                *{get_words_and_links(session, link) for link in links},
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.exception(result)
                    db.add_failed(list(links)[i])
                    continue

                db.add_result(list(links)[i], result)


if __name__ == "__main__":
    asyncio.run(main())
