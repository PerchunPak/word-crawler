import json
import typing as t
import urllib.parse

from loguru import logger

from src.utils import DATA_DIR

if t.TYPE_CHECKING:
    from src.__main__ import SiteResult

DB_FILE = DATA_DIR / "db.json"


def get_domain_name_from_url(url: str) -> str:
    # http://www.example.test/foo/bar -> www.example.test
    netloc = urllib.parse.urlparse(url).netloc
    # -> example.test
    return ".".join(netloc.split(".")[-2:])


class Database:
    def __init__(self) -> None:
        self._words: dict[str, set[str]] = {"__total": set()}
        self._links: dict[str, set[str]] = {"__total": set()}
        self._failed: set[str] = set()
        self._read()

    def _read(self) -> None:
        if not DB_FILE.exists():
            return

        with DB_FILE.open("r") as f:
            as_dict = json.load(f)
            self._words = self._unsanitize(as_dict["words"])
            self._links = self._unsanitize(as_dict["links"])
            self._failed = set(as_dict["failed"])

    def _write(self) -> None:
        with DB_FILE.open("w") as f:
            as_dict = {
                "words": self._sanitize(self._words),
                "links": self._sanitize(self._links),
                "failed": list(self._failed),
            }
            json.dump(as_dict, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _unsanitize(as_dict: dict[str, list[str]]) -> dict[str, set[str]]:
        result = {}
        for key, value in as_dict.items():
            result[key] = set(value)
        return result

    @staticmethod
    def _sanitize(as_dict: dict[str, set[str]]) -> dict[str, list[str]]:
        result = {}
        for key, value in as_dict.items():
            result[key] = list(value)
        return result

    def get_links(self, root_link: str) -> t.Iterator[str]:
        while True:
            all_links = self._links["__total"].copy()
            for link in all_links:
                if (link not in self._words or link not in self._links) and (
                    link not in self._failed
                ):
                    if get_domain_name_from_url(root_link) not in link:
                        logger.warning(f"{link!r} is not valid!")
                        self.add_failed(link)
                        continue
                    if link.endswith(".jpg") or link.endswith(".png"):
                        logger.warning(f"{link!r} is an image, not parsing")
                        self.add_failed(link)
                        continue
                    yield link
            else:
                break

    def add_words(self, site: str, words: set[str]) -> None:
        self._words[site] = words
        self._words["__total"] = self._words["__total"].union(words)
        self._write()

    def add_links(self, site: str, links: set[str]) -> None:
        self._links[site] = links
        self._links["__total"] = self._links["__total"].union(links)
        self._write()

    def add_result(self, site: str, result: "SiteResult") -> None:
        self.add_words(site, result.words)
        self.add_links(site, result.links)

    def add_failed(self, site: str) -> None:
        self._failed.add(site)
        self._write()
