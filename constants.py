from pathlib import Path
import platformdirs


VIDEOS_DIR = Path(platformdirs.user_videos_dir())

NEWSBOAT_DB_PATH = Path(platformdirs.user_data_dir()) / "newsboat" / "cache.db"

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.toml"
