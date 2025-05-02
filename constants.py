from pathlib import Path
import platformdirs


VIDEOS_DIR = Path(platformdirs.user_videos_dir())
TEMP_DIR = VIDEOS_DIR / "tmp_downloads"

NEWSBOAT_DB_PATH = Path(platformdirs.user_data_dir()) / "newsboat" / "cache.db"

YDL_OPTS = {
    "format": "bestvideo[height<=2160]+bestaudio/best",
    "merge_output_format": "mkv",
    "outtmpl": str(TEMP_DIR / "%(uploader)s" / "%(title)s.%(ext)s"),
    "embed-metadata": True,
    "embed-chapters": True,
}
