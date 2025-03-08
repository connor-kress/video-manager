import subprocess
import sys
from typing import Optional
from pathlib import Path
from pymediainfo import MediaInfo

from download import DEST_DIR, Metadata, get_video_path, send_notif

def read_metadata(file_path: Path) -> Optional[Metadata]:
    media_info = MediaInfo.parse(file_path)
    if isinstance(media_info, str):
        return None
    for track in media_info.tracks:
        if track.track_type == 'General':
            metadata = Metadata(
                url=track.url,
                title=track.title,
                artist=track.artist,
            )
            return metadata
    return None


def get_path_to_video_recursive(base_dir: Path, url: str) -> Optional[Path]:
    for file_path in base_dir.rglob('*.mkv'):
        print(file_path)
        metadata = read_metadata(file_path)
        print(metadata)
        if metadata is not None and metadata.url == url:
            return file_path
    return None


def stream_video(url: str) -> None:
    try:
        subprocess.run(['mpv', url], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        if 'members-only' in str(e.stderr):
            send_notif('Error: Members Only', f'Members only video: {url}')
        else:
            send_notif('Error', f'Error streaming video: {url} {e.stderr}')
        raise e


def play_file(file_path: Path) -> None:
    subprocess.run(['mpv', file_path])


def main() -> None:
    if len(sys.argv) != 2:
        send_notif('Error', f'Invalid arguments: {sys.argv[1:]}')
        sys.exit(1)
    url = sys.argv[1]

    # file_path = get_path_to_video_recursive(DEST_DIR, url)
    file_path = get_video_path(url)
    if file_path is not None:
        # send_notif('Found video', str(file_path))
        print(f'Found video {str(file_path)}')
        play_file(file_path)
    else:
        # send_notif('Streaming video', url)
        print(f'Streaming video {url}')
        stream_video(url)


if __name__ == '__main__':
    main()
