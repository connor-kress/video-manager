import argparse
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any

from feedgen.feed import FeedGenerator
import yt_dlp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a playlist with yt-dlp and write an Atom feed."
    )
    parser.add_argument("playlist_url", help="Playlist URL to scrape")
    parser.add_argument("output_path", help="Destination Atom feed file path")
    return parser.parse_args()


def stable_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"urn:sha256:{digest}"


def parse_upload_date(upload_date: str | None) -> datetime | None:
    if upload_date is None:
        return None
    try:
        return datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def get_datetime(entry: dict[str, Any], *keys: str) -> datetime | None:
    for key in keys:
        value = entry.get(key)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str) and key == "upload_date":
            parsed = parse_upload_date(value)
            if parsed is not None:
                return parsed
    return None


def get_entry_url(entry: dict[str, Any]) -> str | None:
    webpage_url = entry.get("webpage_url")
    if isinstance(webpage_url, str) and webpage_url:
        return webpage_url

    original_url = entry.get("original_url")
    if isinstance(original_url, str) and original_url:
        return original_url

    entry_url = entry.get("url")
    if isinstance(entry_url, str) and entry_url.startswith(
        ("http://", "https://")
    ):
        return entry_url

    video_id = entry.get("id")
    extractor = entry.get("extractor_key")
    if isinstance(video_id, str) and extractor == "Youtube":
        return f"https://www.youtube.com/watch?v={video_id}"

    return None


def get_entry_summary(entry: dict[str, Any]) -> str | None:
    description = entry.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()

    uploader = entry.get("uploader") or entry.get("channel")
    duration = entry.get("duration_string")
    pieces = [
        piece
        for piece in (uploader, duration)
        if isinstance(piece, str) and piece
    ]
    if not pieces:
        return None
    return " | ".join(pieces)


def extract_playlist(url: str) -> dict[str, Any]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extract_flat": False,
        "cookiesfrombrowser": ("firefox",),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("START EXTRACTION")
            info = ydl.extract_info(url, download=False)
            print("END EXTRACTION")
        except yt_dlp.DownloadError as error:
            raise RuntimeError(error.msg) from error

    if info is None:
        raise RuntimeError(f"Failed to extract playlist metadata from {url}")

    entries = info.get("entries")
    if entries is None:
        raise RuntimeError(
            "Provided URL did not resolve to a playlist with entries"
        )
    info["entries"] = list(entries)

    return info


def build_feed(playlist: dict[str, Any], playlist_url: str) -> FeedGenerator:
    entries = [
        entry for entry in playlist["entries"] if isinstance(entry, dict)
    ]
    if not entries:
        raise RuntimeError("Playlist did not contain any usable entries")

    feed_url = (
        playlist.get("webpage_url")
        or playlist.get("original_url")
        or playlist_url
    )
    feed_title = playlist.get("title") or playlist.get("id") or playlist_url
    feed_description = (
        playlist.get("description")
        or playlist.get("playlist_description")
        or f"Playlist feed for {feed_title}"
    )
    feed_author = (
        playlist.get("uploader")
        or playlist.get("channel")
        or playlist.get("extractor")
    )

    updated_candidates = [
        dt
        for entry in entries
        for dt in [
            get_datetime(
                entry,
                "modified_timestamp",
                "release_timestamp",
                "timestamp",
                "upload_date",
            )
        ]
        if dt is not None
    ]
    feed_updated = max(updated_candidates, default=datetime.now(UTC))

    fg = FeedGenerator()
    fg.id(feed_url if isinstance(feed_url, str) else stable_id(playlist_url))
    fg.title(str(feed_title))
    fg.link(href=playlist_url, rel="alternate")
    fg.updated(feed_updated)
    fg.subtitle(str(feed_description))

    if isinstance(feed_author, str) and feed_author:
        fg.author({"name": feed_author})

    for index, entry in enumerate(entries, start=1):
        entry_url = get_entry_url(entry)
        entry_title = entry.get("title") or entry.get("id") or f"Entry {index}"
        entry_id = entry_url or stable_id(
            f"{playlist_url}#{entry.get('id', index)}"
        )
        published = get_datetime(
            entry, "release_timestamp", "timestamp", "upload_date"
        )
        updated = get_datetime(
            entry,
            "modified_timestamp",
            "release_timestamp",
            "timestamp",
            "upload_date",
        )
        summary = get_entry_summary(entry)
        author = entry.get("uploader") or entry.get("channel")

        feed_entry = fg.add_entry()
        feed_entry.id(entry_id)
        feed_entry.title(str(entry_title))
        if entry_url is not None:
            feed_entry.link(href=entry_url)
        if updated is not None:
            feed_entry.updated(updated)
        elif published is not None:
            feed_entry.updated(published)
        else:
            feed_entry.updated(feed_updated)
        if published is not None:
            feed_entry.published(published)
        if isinstance(summary, str) and summary:
            feed_entry.summary(summary)
        if isinstance(author, str) and author:
            feed_entry.author({"name": author})

    return fg


def main() -> None:
    args = parse_args()
    try:
        playlist = extract_playlist(args.playlist_url)
        feed = build_feed(playlist, args.playlist_url)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    feed.atom_file(str(output_path), pretty=True)


if __name__ == "__main__":
    main()
