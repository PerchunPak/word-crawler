import json
import typing as t

from src.utils import DATA_DIR

if t.TYPE_CHECKING:
    from src.__main__ import SiteResult

DB_FILE = DATA_DIR / "db.json"


class Database:
    def __init__(self) -> None:
        self._words: dict[str, set[str]] = {"__total": set()}
        self._links: dict[str, set[str]] = {"__total": set()}
        self._visited_links: set[str] = set()
        self._read()

    def _read(self) -> None:
        if not DB_FILE.exists():
            return

        with DB_FILE.open("r") as f:
            as_dict = json.load(f)
            self._words = self._unsanitize(as_dict["words"])
            self._links = self._unsanitize(as_dict["links"])
            self._visited_links = set(as_dict["visited_links"])

    def _write(self) -> None:
        with DB_FILE.open("w") as f:
            as_dict = {
                "words": self._sanitize(self._words),
                "links": self._sanitize(self._links),
                "visited_links": list(self._visited_links),
            }
            json.dump(as_dict, f)

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

    def get_links(self) -> t.Iterator[str]:
        found_unvisited_link = True
        while found_unvisited_link:
            found_unvisited_link = False

            all_links = self._links["__total"].copy()
            for link in all_links:
                if link not in self._visited_links:
                    found_unvisited_link = True
                    yield link
                    self._visited_links.add(link)

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
