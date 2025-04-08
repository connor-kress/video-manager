import sqlite3
import sys
from pathlib import Path
from dataclasses import dataclass

NEWSBOAT_DB_PATH = Path.home() / ".local" / "share" / "newsboat" / "cache.db"


@dataclass
class Metadata:
    url: str
    title: str
    author: str
    feed_title: str


def extract_newsboat_data_raw(cur: sqlite3.Cursor, url: str) -> Metadata:
    cur.execute("""
    SELECT i.title, i.author, f.title
    FROM rss_item i
    JOIN rss_feed f ON i.feedurl = f.rssurl
    WHERE i.url = ?
    """, (url,))
    title, author, feed_title = cur.fetchone()
    return Metadata(url, title, author, feed_title)


def extract_newsboat_data(url: str) -> Metadata:
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
