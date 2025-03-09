import subprocess
import sys
from pathlib import Path

from database import get_video
from download import send_notif


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

    file_path, metadata = get_video(url)
    if file_path is not None:
        assert metadata is not None
        # send_notif('Found video', metadata.title)
        print(f'Found video: {metadata.title}')
        play_file(file_path)
    else:
        # send_notif('Streaming video', url)
        print(f'Streaming video: {url}')
        stream_video(url)


if __name__ == '__main__':
    main()
