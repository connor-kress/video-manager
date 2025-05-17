import sqlite3
import sys
from dataclasses import dataclass
from typing import Optional

from constants import NEWSBOAT_DB_PATH
from database import Metadata


@dataclass
class NewsboatData:
    url: str
    title: str
    author: str
    feed_title: str


def extract_newsboat_data_raw(
    cur: sqlite3.Cursor, url: str
) -> Optional[NewsboatData]:
    cur.execute("""
    SELECT i.title, i.author, f.title AS feed_title
    FROM rss_item i
    JOIN rss_feed f ON i.feedurl = f.rssurl
    WHERE i.url = ?
    """, (url,))
    row = cur.fetchone()
    if row is None:
        return None
    title, author, feed_title = row
    metadata = NewsboatData(url, title, author, feed_title)
    return metadata


def extract_newsboat_data(url: str) -> Optional[NewsboatData]:
    if not NEWSBOAT_DB_PATH.is_file():
        return None
    with sqlite3.connect(NEWSBOAT_DB_PATH) as conn:
        cur = conn.cursor()
        return extract_newsboat_data_raw(cur, url)


def get_metadata_from_newsboat(url: str) -> Optional[Metadata]:
    newsboat_data = extract_newsboat_data(url)
    if newsboat_data is None:
        return None
    return Metadata(
        url=url,
        title=newsboat_data.title,
        artist=newsboat_data.feed_title,
    )


def main() -> None:
    if len(sys.argv) != 2:
        print("Please provide one video url.", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    metadata = extract_newsboat_data(url)
    print(metadata)


if __name__ == "__main__":
    main()
