import argparse
import hashlib
import os
import pathlib

from config import EXTENSION, ARGUMENT_DESCRIPTIONS
from misc import log


def insufficient_content_size() -> None:
    log("Validation failed: insufficient content size", 31)


def validate(path: str, log_details: bool = False) -> bool:
    path = os.path.abspath(path)
    path_obj: pathlib.Path = pathlib.Path(path)
    if not path_obj.exists():
        log(f"Validation failed: input path must lead to an existing file or folder", 31)
        return False
    elif path == path.removesuffix(f".{EXTENSION}"):
        log(f"Unpacking failed: input path must end with \".{EXTENSION}\"", 31)
        return False

    content: bytes = b""
    with open(path, "rb") as file:
        content: bytes = file.read()

    if len(content) < 32:
        if log_details:
            insufficient_content_size()
        return False
    checksum: bytes = content[:32]
    content = content[32:]
    content_hash: bytes = hashlib.sha256(content).digest()
    if content_hash != checksum:
        if log_details:
            log("Validation failed: checksums did not match", 31)
        return False

    location: list[int] = []
    while content:
        item_name_length: int = int.from_bytes(content[:1])
        content = content[1:]
        if len(content) < item_name_length:
            if log_details:
                insufficient_content_size()
            return False
        item_name: str = content[:item_name_length].decode("UTF-8")
        content = content[item_name_length:]

        if len(location) > 0:
            location[-1] -= 1

            if location[-1] == 0:
                location.pop()

        if "." not in item_name:
            if len(content) < 4:
                if log_details:
                    insufficient_content_size()
                return False
            folder_item_count: int = int.from_bytes(content[:4])
            content = content[4:]
            location.append(folder_item_count)
        else:
            if len(content) < 8:
                if log_details:
                    insufficient_content_size()
                return False
            file_content_size: int = int.from_bytes(content[:8])
            content = content[8:]
            if len(content) < file_content_size:
                if log_details:
                    insufficient_content_size()
                return False
            content = content[file_content_size:]

    if len(location) > 0:
        if log_details:
            log("Validation failed: file tree is incorrect", 31)
        return False

    if log_details:
        log("Validation successful", 32)
    return True


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        default=os.getcwd(),
        type=str,
        help=ARGUMENT_DESCRIPTIONS["path"],
    )
    args: argparse.Namespace = parser.parse_args()

    validate(args.path, log_details=True)


if __name__ == "__main__":
    main()
