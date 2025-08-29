import sys
from config import load_config
from constants import CONFIG_PATH
from database import Metadata
from download import set_props
from models import LinkType
from pathlib import Path


def main() -> None:
    config = load_config(CONFIG_PATH)
    if config is None:
        sys.exit(1)

    argv = sys.argv
    print(f"{argv=}")
    if len(argv) != 6:  # 5 + 1 for program name
        print("Invalid number of args")
        sys.exit(1)

    in_arg, out_arg = argv[1], argv[2]
    metadata = Metadata(
        url=argv[3],
        title=argv[4],
        artist=argv[5],
    )

    in_path = Path(in_arg)
    out_path = Path(out_arg)

    set_props(in_path, out_path, metadata, LinkType.DEFAULT, config)


if __name__ == "__main__":
    main()
