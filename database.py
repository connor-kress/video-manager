from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional

from constants import DEST_DIR


DEST_DIR.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DEST_DIR / 'metadata.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS videos (
    url TEXT NOT NULL UNIQUE PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    artist TEXT NOT NULL
);
""")
conn.commit()


@dataclass
class Metadata:
    url: str
    title: str
    artist: str


def insert_video(path: Path, metadata: Metadata) -> None:
    cur.execute(
        """
        INSERT INTO videos (path, url, title, artist)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            path = excluded.path,
            title = excluded.title,
            artist = excluded.artist
        ON CONFLICT(path) DO UPDATE SET
            url = excluded.url,
            title = excluded.title,
            artist = excluded.artist;
        """,
        (str(path), metadata.url, metadata.title, metadata.artist),
    )
    conn.commit()


def get_video(url: str) -> tuple[Optional[Path], Optional[Metadata]]:
    cur.execute(
        'SELECT path, url, title, artist FROM videos WHERE url = ?;', (url,)
    )
    row = cur.fetchone()
    if row is None:
        print('Video not found')
        return None, None
    assert len(row) == 4
    path_str = row[0]
    path = Path(path_str)
    metadata = Metadata(
        url=row[1],
        title=row[2],
        artist=row[3],
    )
    if not path.is_file():
        print(f'Deleted entry: {path_str}')
        return None, metadata
    print(f'Video found: {path_str}')
    return path, metadata


def get_all_videos() -> list[tuple[Path, Metadata]]:
    cur.execute('SELECT path, url, title, artist FROM videos;')
    rows = cur.fetchall()
    videos = list[tuple[Path, Metadata]]()
    for row in rows:
        assert len(row) == 4
        videos.append((
            Path(row[0]),
            Metadata(
                url=row[1],
                title=row[2],
                artist=row[3],
            ),
        ))
    return videos
