import subprocess
from pathlib import Path
from typing import Optional
from pymediainfo import MediaInfo
from database import Metadata


# TODO: add link to file for download complete notification
def send_notif(title: str, msg: str) -> None:
    subprocess.run(['notify-send', '--hint=int:transient:1',
                    '--urgency=normal', title, msg])


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
