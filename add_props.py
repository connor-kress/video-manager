from sys import argv, exit
from pathlib import Path

from database import Metadata
from download import set_props


def main() -> None:
    print(f"{argv=}")
    if len(argv) != 6:  # 5 + 1 for program name
        print("Invalid number of args")
        exit(1)

    in_arg, out_arg = argv[1], argv[2]
    metadata = Metadata(
        url=argv[3],
        title=argv[4],
        artist=argv[5],
    )

    in_path = Path(in_arg)
    out_path = Path(out_arg)

    set_props(in_path, out_path, metadata)


if __name__ == "__main__":
    main()
