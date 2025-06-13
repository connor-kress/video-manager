from pathlib import Path
import sqlite3
from typing import Optional

from constants import VIDEOS_DIR
from models import Metadata
from util import get_pid_and_stime, process_exists


VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(VIDEOS_DIR / "metadata.db")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS videos (
    url TEXT NOT NULL UNIQUE PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    artist TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS downloads_in_progress (
    url TEXT PRIMARY KEY,
    pid INTEGER NOT NULL,
    start_time REAL NOT NULL
);
""")
conn.commit()


def insert_video(path: Path, metadata: Metadata) -> None:
    cur.execute(
        """
        INSERT INTO videos (path, url, title, artist)
        VALUES (?, ?, ?, ?);
        """,
        (str(path), metadata.url, metadata.title, metadata.artist),
    )
    conn.commit()


def get_video(url: str) -> tuple[Optional[Path], Optional[Metadata]]:
    cur.execute(
        "SELECT path, url, title, artist FROM videos WHERE url = ?;", (url,)
    )
    row = cur.fetchone()
    if row is None:
        # print("Video not found")
        return None, None
    path_str, url, title, artist = row
    path = Path(path_str)
    metadata = Metadata(
        url=url,
        title=title,
        artist=artist,
    )
    if not path.is_file():
        print(f"Removing deleted entry: {artist} - {title}")
        delete_video(url)
        return None, metadata
    # print(f"Video found: {path_str}")
    return path, metadata


def get_all_videos() -> list[tuple[Path, Metadata]]:
    cur.execute("SELECT path, url, title, artist FROM videos;")
    videos = []
    for path, url, title, artist in cur.fetchall():
        videos.append((
            Path(path),
            Metadata(
                url=url,
                title=title,
                artist=artist,
            ),
        ))
    return videos


def delete_video(url: str) -> None:
    cur.execute("DELETE FROM videos WHERE url = ?;", (url,))
    conn.commit()


def remove_stale_entries() -> None:
    """Deletes rows whose PID is no longer running or whose
    creation_time doesn't match.
    """
    cur.execute("SELECT url, pid, start_time FROM downloads_in_progress")
    for url, pid, stime in cur.fetchall():
        if not process_exists(pid, stime):
            cur.execute(
                "DELETE FROM downloads_in_progress WHERE url = ?",
                (url,)
            )
    conn.commit()


def try_reserve_url(url: str) -> bool:
    """Returns True if we successfully reserved this URL for download,
   False if it is already in-progress.
   """
    pid, stime = get_pid_and_stime()
    remove_stale_entries()
    try:
        cur.execute(
            "INSERT INTO downloads_in_progress(url, pid, start_time) "
            "VALUES (?, ?, ?)",
            (url, pid, stime)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Download already in-progress
        return False


def clear_reservation(url: str) -> None:
    cur.execute(
        "DELETE FROM downloads_in_progress WHERE url = ?",
        (url,)
    )
    conn.commit()
