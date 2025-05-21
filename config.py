from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import toml

from constants import CONFIG_PATH
from util import send_notif


class FeaturesConfig(BaseModel):
    enable_zoom_reencoding: bool = Field(default=False)


class Config(BaseModel):
    features: FeaturesConfig


def load_config(config_path: Path) -> Optional[Config]:
    """Loads configuration from a TOML file and parses it
    into a Config object.
    """
    try:
        with open(config_path, "r") as f:
            config_data = toml.load(f)
        return Config(**config_data)
    except FileNotFoundError:
        send_notif("Config Error",
                   f"Configuration file not found at {config_path}")
        print(f"Configuration file not found at {config_path}")
    except toml.TomlDecodeError as e:
        send_notif("Config Error", "Error decoding TOML file")
        print(f"Error decoding TOML file: {e}")
    except Exception as e:
        send_notif("Config Error", "Error decoding TOML file")
        print(f"Error loading or parsing configuration: {e}")
    return None


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)
    print(config)
