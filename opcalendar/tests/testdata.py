import json
from pathlib import Path


def _load_testdata() -> dict:
    testdata_path = Path(__file__).parent / "testdata.json"
    with testdata_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


_testdata = _load_testdata()


class FeedsStub:
    class FeedEntryStub:
        class AuthorDetail:
            def __init__(self, author_detail) -> None:
                self.name = author_detail.get("name", "") if author_detail else ""

        def __init__(self, entry) -> None:
            self.author_detail = self.AuthorDetail(entry.get("author_detail"))
            self.title = entry.get("title", "")
            self.published = entry.get("published", "")
            self.description = entry.get("description", "")

    def __init__(self, feed) -> None:
        self.entries = [self.FeedEntryStub(row) for row in feed["entries"]]


def feedparser_parse(url) -> list:
    return FeedsStub(_testdata["feeds"].get(url))
