import os
import pathlib
import statx
import subprocess
import sys

from typing import Callable


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
    path = os.path.abspath(path)

    # Windows
    if sys.platform == "win32":
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


def is_hidden(path: str) -> bool:
    path = os.path.abspath(path)

    if sys.platform == "win32":
        # Tries to get hidden flag
        try:
            import ctypes
            get_attributes: Callable[[str], int] = getattr(ctypes.windll.kernel32, "GetFileAttributesW")
            attributes: int = get_attributes(str(path))
            if attributes == -1:
                return False
            return bool(attributes & 2)
        except:
            return False

    # If item name starts with dot
    return os.path.basename(os.path.abspath(path)).startswith(".")


def hide(path: str) -> None:
    path = os.path.abspath(path)

    if sys.platform == "win32":
        subprocess.run(["attrib", "+H", path])

    elif sys.platform == "darwin":
        subprocess.run(["chflags", "hidden", path], check=True)
