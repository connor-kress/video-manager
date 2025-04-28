from pathlib import Path
import platformdirs


TEMP_DIR = Path(platformdirs.user_videos_dir()) / 'tmp_downloads'
DEST_DIR = Path(platformdirs.user_videos_dir())
