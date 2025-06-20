import os
import platform
import re
import psutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from pymediainfo import MediaInfo

from models import LinkType, Metadata


def get_link_type(url: str) -> LinkType:
    zoom_pattern = re.compile(r"https://([\w-]+\.)?zoom\.us/.*")
    mediasite_pattern = re.compile(r"https://mediasite\.video\.ufl\.edu/.*")
    if zoom_pattern.match(url):
        return LinkType.ZOOM
    elif mediasite_pattern.match(url):
        return LinkType.MEDIASITE
    else:
        return LinkType.DEFAULT


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
        pass
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


def get_pid_and_stime() -> tuple[int, float]:
    pid = os.getpid()
    stime = psutil.Process(pid).create_time()
    return pid, stime


def process_exists(pid: int, stime: float) -> bool:
    try:
        p = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    # exists if create time matches
    return abs(p.create_time() - stime) <= 1.0


def remove_dir_if_empty(dir_path: Path) -> None:
    if not dir_path.is_dir():
        return
    for _ in dir_path.iterdir():
        return
    dir_path.rmdir()


def read_urls_from_file(file_path: Path) -> Optional[list[str]]:
    if not file_path.is_file():
        send_notif("Error", f"File does not exist: {file_path}")
        return None
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]
