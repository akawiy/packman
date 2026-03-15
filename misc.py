import os
import pathlib

from config import ANSI_COLORS


def log(text: str, color_code: int | None = None) -> None:
    if not ANSI_COLORS or color_code is None:
        print(text)
        return
    print(f"\033[{color_code}m{text}\033[0m")


def list_folder(path: str) -> list[str]:
    path = os.path.abspath(path)

    folders: list[str] = []
    files: list[str] = []

    for item_name in os.listdir(path):
        item_path: str = os.path.join(path, item_name)
        item_path_obj: pathlib.Path = pathlib.Path(item_path)

        if item_path_obj.is_dir():
            folders.append(item_path)
            folders.extend(list_folder(item_path))
        elif item_path_obj.is_file():
            files.append(item_path)

    return folders + files
