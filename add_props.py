from sys import argv, exit
from pathlib import Path
from download import set_props

def main() -> None:
    print(f"{argv=}")
    if len(argv) != 6:  # 5 + 1 for program name
        print("Invalid number of args")
        exit(1)

    in_arg, out_arg = argv[1], argv[2]
    url, title, artist = argv[3:]

    in_path = Path(in_arg)
    out_path = Path(out_arg)

    set_props(in_path, out_path, url, title, artist)
    # "https://ufl.instructure.com/courses/525435/files/95194725?module_item_id=11820556", "Divide and Conquer Review", "Christina Boucher"

if __name__ == "__main__":
    main()
