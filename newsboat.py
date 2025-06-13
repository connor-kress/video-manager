import sqlite3
import sys
from typing import Optional

from constants import NEWSBOAT_DB_PATH
from database import Metadata
from models import NewsboatFeed, NewsboatItem


def item_to_video_metadata(item: NewsboatItem) -> Metadata:
    return Metadata(
        url=item.url,
        title=item.title,
        artist=item.feed_title,
    )


def fetch_newsboat_item_raw(
    cur: sqlite3.Cursor, url: str
) -> Optional[NewsboatItem]:
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
    item = NewsboatItem(
        url=url,
        title=title,
        author=author,
        feed_title=feed_title,
    )
    return item


def fetch_newsboat_items_by_feed_raw(
    cur: sqlite3.Cursor, feed: NewsboatFeed
) -> list[NewsboatItem]:
    cur.execute("""
    SELECT url, title, author
    FROM rss_item
    WHERE feedurl = ?
    """, (feed.rssurl,))
    items = []
    for url, title, author in cur.fetchall():
        items.append(NewsboatItem(
            url=url,
            title=title,
            author=author,
            feed_title=feed.title,
        ))
    return items


def fetch_newsboat_feed_raw(
    cur: sqlite3.Cursor, url: str
) -> Optional[NewsboatFeed]:
    cur.execute("""
    SELECT title, rssurl
    FROM rss_feed
    WHERE url = ?
    """, (url,))
    row = cur.fetchone()
    if row is None:
        return None
    title, rssurl = row
    feed = NewsboatFeed(url=url, rssurl=rssurl, title=title)
    return feed


def fetch_newsboat_item(url: str) -> Optional[NewsboatItem]:
    if not NEWSBOAT_DB_PATH.is_file():
        return None
    with sqlite3.connect(NEWSBOAT_DB_PATH) as conn:
        cur = conn.cursor()
        return fetch_newsboat_item_raw(cur, url)


def fetch_newsboat_feed_and_items(
    feed_url: str
) -> tuple[Optional[NewsboatFeed], list[NewsboatItem]]:
    if not NEWSBOAT_DB_PATH.is_file():
        return None, []
    with sqlite3.connect(NEWSBOAT_DB_PATH) as conn:
        cur = conn.cursor()
        feed = fetch_newsboat_feed_raw(cur, feed_url)
        if feed is None:
            return None, []
        items = fetch_newsboat_items_by_feed_raw(cur, feed)
        return feed, items


def get_metadata_from_newsboat(url: str) -> Optional[Metadata]:
    item = fetch_newsboat_item(url)
    if item is None:
        return None
    return item_to_video_metadata(item)


def get_feed_and_items_from_newsboat(
    feed_url: str
) -> tuple[Optional[NewsboatFeed], list[Metadata]]:
    feed, items = fetch_newsboat_feed_and_items(feed_url)
    if feed is None:
        return None, []
    return feed, list(map(item_to_video_metadata, items))


def main() -> None:
    if len(sys.argv) != 2:
        print("Please provide one video url.", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    item = fetch_newsboat_item(url)
    print(item)


if __name__ == "__main__":
    main()
