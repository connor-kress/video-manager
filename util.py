import subprocess
from pathlib import Path
import platform
import sys
from typing import Optional
from pymediainfo import MediaInfo
from database import Metadata


# TODO: add link to file for download complete notification
def send_notif(title: str, msg: str) -> None:
    system = platform.system()

    if system == "Linux":
        try:
            subprocess.run([
                "notify-send",
                "--hint=int:transient:1",
                "--urgency=normal",
                title,
                msg,
            ], check=True)
        except FileNotFoundError:
            print(f"{title}: {msg}")
            print("`notify-send` not found. "
                  "See README for installation instructions.",
                  file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error running notify-send: {e}", file=sys.stderr)

    elif system == "Darwin":
        try:
            subprocess.run([
                "terminal-notifier",
                "-title",
                title,
                "-message",
                msg,
            ], check=True)
        except FileNotFoundError:
            print(f"{title}: {msg}")
            print("`terminal-notifier` not found. "
                  "See README for installation instructions.",
                  file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error running terminal-notifier: {e}", file=sys.stderr)

    else:  # system == "Windows":
        print(f"{title}: {msg}")


def read_metadata(file_path: Path) -> Optional[Metadata]:
    media_info = MediaInfo.parse(file_path)
    if isinstance(media_info, str):
        return None
    for track in media_info.tracks:
        if track.track_type == "General":
            metadata = Metadata(
                url=track.url,
                title=track.title,
                artist=track.artist,
            )
            return metadata
    return None
