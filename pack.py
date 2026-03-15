import argparse
import hashlib
import os
import pathlib
import time

from config import EXTENSION, ARGUMENT_DESCRIPTIONS
from misc import log, list_folder
from validate import validate


def pack_item(path: str) -> bytes:
    path = os.path.abspath(path)
    path_obj: pathlib.Path = pathlib.Path(path)

    result: bytes = b""

    item_name: bytes = path_obj.name.encode("UTF-8")
    item_name_length: bytes = len(item_name).to_bytes(1)
    result += item_name_length + item_name

    if path_obj.is_dir():
        folder_item_count: bytes = len(os.listdir(path)).to_bytes(4)
        result += folder_item_count
    elif path_obj.is_file():
        with open(path, "rb") as file:
            file_content: bytes = file.read()
        file_content_size: bytes = len(file_content).to_bytes(8)
        result += file_content_size + file_content

    return result


def pack(path_in: str, path_out: str | None = None, log_details: bool = False) -> None:
    start_time: float = time.time()

    path_in = os.path.abspath(path_in)
    path_in_obj: pathlib.Path = pathlib.Path(path_in)
    if not path_in_obj.exists():
        log(f"Packing failed: input path must lead to an existing file or folder", 31)
        return
    if path_out is None:
        path_out = os.path.join(os.getcwd(), f"{path_in_obj.stem}.{EXTENSION}")
    elif path_out == path_out.removesuffix(f".{EXTENSION}"):
        log(f"Packing failed: output path must end with \".{EXTENSION}\"", 31)
        return
    path_out = os.path.abspath(path_out)

    items: list[str] = [path_in] + list_folder(path_in)
    result: bytes = b""

    for index, item_path in enumerate(items):
        if log_details:
            log(f"Packing {(index / len(items)):.1%} \"{item_path.replace('\\', '/')}\"")
        result += pack_item(item_path)

    checksum: bytes = hashlib.sha256(result).digest()
    result = checksum + result

    with open(path_out, "wb") as file:
        file.write(result)

    if not validate(path_out, log_details=log_details):
        return

    if log_details:
        end_time: float = time.time()
        time_difference: float = end_time - start_time
        log(f"Packing complete ({time_difference:.3f}s)", 32)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        default=os.getcwd(),
        type=str,
        help=ARGUMENT_DESCRIPTIONS["path"],
    )
    parser.add_argument(
        "-o",
        default=None,
        type=str,
        required=False,
        help=ARGUMENT_DESCRIPTIONS["-o"],
    )
    args: argparse.Namespace = parser.parse_args()

    pack(args.path, path_out=args.o, log_details=True)


if __name__ == "__main__":
    main()
