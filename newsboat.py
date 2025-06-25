import sqlite3
import sys
from datetime import datetime
from typing import Optional

from constants import NEWSBOAT_DB_PATH
from database import Metadata
from models import NewsboatFeed, NewsboatItem

# Newsboat schema for reference
#
# CREATE TABLE rss_feed (
#     rssurl VARCHAR(1024) PRIMARY KEY NOT NULL,
#     url VARCHAR(1024) NOT NULL,
#     title VARCHAR(1024) NOT NULL,
#     lastmodified INTEGER(11) NOT NULL DEFAULT 0,
#     is_rtl INTEGER(1) NOT NULL DEFAULT 0,
#     etag VARCHAR(128) NOT NULL DEFAULT ""
# );
#
# CREATE TABLE rss_item (
#     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
#     guid VARCHAR(64) NOT NULL,
#     title VARCHAR(1024) NOT NULL,
#     author VARCHAR(1024) NOT NULL,
#     url VARCHAR(1024) NOT NULL,
#     feedurl VARCHAR(1024) NOT NULL,
#     pubDate INTEGER NOT NULL,
#     content VARCHAR(65535) NOT NULL,
#     unread INTEGER(1) NOT NULL,
#     enclosure_url VARCHAR(1024),
#     enclosure_type VARCHAR(1024),
#     enqueued INTEGER(1) NOT NULL DEFAULT 0,
#     flags VARCHAR(52),
#     deleted INTEGER(1) NOT NULL DEFAULT 0,
#     base VARCHAR(128) NOT NULL DEFAULT "",
#     content_mime_type VARCHAR(255) NOT NULL DEFAULT "",
#     enclosure_description VARCHAR(1024) NOT NULL DEFAULT "",
#     enclosure_description_mime_type VARCHAR(128) NOT NULL DEFAULT ""
# );


def newsboat_to_video_metadata(item: NewsboatItem) -> Metadata:
    return Metadata(
        url=item.url,
        title=item.title,
        artist=item.feed_title,
    )


def fetch_newsboat_item_raw(
    cur: sqlite3.Cursor, url: str
) -> Optional[NewsboatItem]:
    cur.execute("""
    SELECT i.title, i.author, i.pubDate, i.content, i.unread,
           f.title AS feed_title
    FROM rss_item i
    JOIN rss_feed f ON i.feedurl = f.rssurl
    WHERE i.url = ?
    """, (url,))
    row = cur.fetchone()
    if row is None:
        return None
    title, author, pub_date, content, unread, feed_title = row
    item = NewsboatItem(
        url=url,
        title=title,
        author=author,
        pub_date=datetime.fromtimestamp(pub_date),
        content=content,
        unread=bool(unread),
        feed_title=feed_title,
    )
    return item


def fetch_newsboat_items_by_feed_raw(
    cur: sqlite3.Cursor, feed: NewsboatFeed
) -> list[NewsboatItem]:
    cur.execute("""
    SELECT url, title, author, pubDate, content, unread
    FROM rss_item
    WHERE feedurl = ?
    """, (feed.rssurl,))
    items = []
    for url, title, author, pub_date, content, unread in cur.fetchall():
        items.append(NewsboatItem(
            url=url,
            title=title,
            author=author,
            pub_date=datetime.fromtimestamp(pub_date),
            content=content,
            unread=bool(unread),
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
    return newsboat_to_video_metadata(item)


def get_feed_and_items_from_newsboat(
    feed_url: str
) -> tuple[Optional[NewsboatFeed], list[Metadata]]:
    feed, items = fetch_newsboat_feed_and_items(feed_url)
    if feed is None:
        return None, []
    return feed, list(map(newsboat_to_video_metadata, items))


def main() -> None:
    if len(sys.argv) != 2:
        print("Please provide one video url.", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    item = fetch_newsboat_item(url)
    print(item)


if __name__ == "__main__":
    main()
