from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from typing import Optional
import yt_dlp
from yt_dlp.utils import sanitize_filename

TEMP_DIR = Path.home() / 'Videos' / 'tmp_downloads'
DEST_DIR = Path.home() / 'Videos' / 'Youtube'
DEST_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DEST_DIR / 'metadata.db')
cur = conn.cursor()


@dataclass
class Metadata:
    url: str
    title: str
    artist: str


cur.execute("""
CREATE TABLE IF NOT EXISTS videos (
    url TEXT NOT NULL UNIQUE PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    artist TEXT NOT NULL
);
""")
conn.commit()

YDL_OPTS = {
    'format': 'bestvideo[height<=2160]+bestaudio/best',
    'merge_output_format': 'mkv',
    'outtmpl': str(TEMP_DIR / '%(uploader)s' / '%(title)s.%(ext)s'),
    'embed-metadata': True,
    'embed-chapters': True,
}


def insert_video(path: Path, metadata: Metadata) -> None:
    cur.execute(
        """
        INSERT INTO videos (url, path, title, artist)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            path = excluded.path,
            title = excluded.title,
            artist = excluded.artist;
        """,
        (metadata.url, str(path), metadata.title, metadata.artist),
    )
    conn.commit()


def get_video_path(url: str) -> Optional[Path]:
    print(f'Searching for {url}')
    cur.execute('SELECT path FROM videos WHERE url = ?;', (url,))
    row = cur.fetchone()
    if row is None:
        print('Video not found')
        return None
    else:
        path_str = row[0]
        assert isinstance(path_str, str)
        path = Path(path_str)
        if not path.is_file():
            print(f'Deleted entry: {path_str}')
            return None
        print(f'Video found: {path_str}')
        return path


def is_zoom_link(url: str) -> bool:
    zoom_pattern = re.compile(r"https://([\w-]+\.)?zoom\.us/.*")
    return bool(zoom_pattern.match(url))


def get_file_paths(info: dict[str, str]) -> tuple[Path, Path]:
    url = info['original_url']
    if is_zoom_link(url):
        file_name = sanitize_filename(f'zoom-{info["id"]}.mkv')  # force mkv
    else:
        file_name = sanitize_filename(f'{info["title"]}.mkv')  # force mkv
    dir_name = sanitize_filename(info.get('uploader', 'Unknown'))
    temp_path = TEMP_DIR / dir_name / file_name
    file_path = DEST_DIR / dir_name / file_name
    return (temp_path, file_path)


# TODO: add link to file for download complete notification
def send_notif(title: str, msg: str) -> None:
    subprocess.run(['notify-send', '--hint=int:transient:1',
                    '--urgency=normal', title, msg])


def set_props( in_path: Path, out_path: Path, metadata: Metadata) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg',
        '-i', in_path,
        '-metadata', f'URL={metadata.url}',
        '-metadata', f'title={metadata.title}',
        '-metadata', f'artist={metadata.artist}',
        '-codec', 'copy',
        out_path,
    ])
    print(f'set url prop to {metadata.url}')


def main() -> None:
    if len(sys.argv) != 2:
        send_notif('Error', f'Invalid arguments: {sys.argv[1:]}')
        sys.exit(1)
    url = sys.argv[1]
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
        if info is None:
            send_notif('Error', f'Error locating video: {url}')
            sys.exit(1)
        metadata = Metadata(
            url=url,
            title = info.get('title', info.get('id', 'Unknown')),
            artist = info.get('uploader', 'Unknown'),
        )
        temp_path, file_path = get_file_paths(info)
        ydl.params['outtmpl']['default'] = str(temp_path)
        if file_path.is_file():  # TODO: check using URL prop
            send_notif('Already Downloaded', metadata.title)
            return
        send_notif('Starting Download', metadata.title)
        try:
            ydl.download([metadata.url])
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
    set_props(temp_path, file_path, metadata)
    insert_video(file_path, metadata)
    send_notif('Finished Download', metadata.title)


if __name__ == '__main__':
    main()
