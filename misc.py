import os
import pathlib
import platform
import statx

from config import ANSI_COLORS


def colored(text: str, color_code: int | None = None) -> str:
    if not ANSI_COLORS or color_code is None:
        return text
    return f"\033[{color_code}m{text}\033[0m"


def list_folder(path: str) -> list[str]:
    path = os.path.abspath(path)

    folders: list[str] = []
    files: list[str] = []

    for item_name in os.listdir(path):
        item_path: str = os.path.join(path, item_name)
        item_path_obj: pathlib.Path = pathlib.Path(item_path)

        if item_path_obj.is_file():
            files.append(item_path)
        elif item_path_obj.is_dir():
            folders.append(item_path)
            folders.extend(list_folder(item_path))

    return folders + files


def get_creation_timestamp(path: str) -> float:
    # Windows
    if platform.system() == "Windows":
        return os.path.getctime(path)

    # Mac / Unix
    try:
        return os.stat(path).st_birthtime
    except AttributeError:
        pass

    # Linux
    creation_datetime: float | None = statx.statx(path).btime
    if creation_datetime is not None:
        return creation_datetime

    # Couldn't get creation datetime so returning modification timestamp
    return os.path.getmtime(path)
