import sqlite3
import sys
from dataclasses import dataclass

from constants import NEWSBOAT_DB_PATH


@dataclass
class NewsboatData:
    url: str
    title: str
    author: str
    feed_title: str


def extract_newsboat_data_raw(cur: sqlite3.Cursor, url: str) -> NewsboatData:
    cur.execute("""
    SELECT i.title, i.author, f.title AS feed_title
    FROM rss_item i
    JOIN rss_feed f ON i.feedurl = f.rssurl
    WHERE i.url = ?
    """, (url,))
    title, author, feed_title = cur.fetchone()
    metadata = NewsboatData(url, title, author, feed_title)
    print(metadata)
    return metadata


def extract_newsboat_data(url: str) -> NewsboatData:
    with sqlite3.connect(NEWSBOAT_DB_PATH) as conn:
        cur = conn.cursor()
        return extract_newsboat_data_raw(cur, url)


def main() -> None:
    if len(sys.argv) != 2:
        print("Please provide one video url.", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    metadata = extract_newsboat_data(url)
    print(metadata)


if __name__ == "__main__":
    main()
