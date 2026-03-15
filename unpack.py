import argparse
import os
import pathlib
import time

from config import ARGUMENT_DESCRIPTIONS
from misc import log
from validate import validate


def unpack(path_in: str, path_out: str | None = None, log_details: bool = False) -> None:
    start_time: float = time.time()

    path_in = os.path.abspath(path_in)
    if path_out is None:
        path_out = os.getcwd()
    path_out = os.path.abspath(path_out)

    if not validate(path_in, log_details=True):
        return

    content: bytes = b""
    with open(path_in, "rb") as file:
        content: bytes = file.read()
    content = content[32:]

    location: list[list[str | int]] = []
    while content:
        item_name_length: int = int.from_bytes(content[:1])
        content = content[1:]
        item_name: str = content[:item_name_length].decode("UTF-8")
        content = content[item_name_length:]
        item_path: str = os.path.join(path_out, *[i[0] for i in location], item_name)
        if log_details:
            log(f"Unpacking \"{item_path.replace("\\", "/")}\"")

        if len(location) > 0:
            location[-1][1] -= 1

            if location[-1][1] == 0:
                location.pop()

        if "." not in item_name:
            folder_item_count: int = int.from_bytes(content[:4])
            content = content[4:]
            location.append([item_name, folder_item_count])
            pathlib.Path(item_path).mkdir(parents=True, exist_ok=True)
        else:
            file_content_size: int = int.from_bytes(content[:8])
            content = content[8:]
            file_content: bytes = content[:file_content_size]
            content = content[file_content_size:]

            with open(item_path, "wb") as file:
                file.write(file_content)

    if log_details:
        end_time: float = time.time()
        time_difference: float = end_time - start_time
        log(f"Unpacking complete ({time_difference:.3f}s)", 32)


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

    unpack(args.path, path_out=args.o, log_details=True)


if __name__ == "__main__":
    main()
