import argparse

from config import PROJECT_NAME, VERSION_STR, VERSION_INT, RELEASE_DATE
from logger import logger, Color
from packing import Packer
from unpacking import Unpacker
from validation import Validator


class Packman:

    @staticmethod
    def pack(path_in: str, path_out: str | None = None, key: str | bytes | None = None) -> None:
        Packer(path_in, path_out=path_out, key=key).pack()

    @staticmethod
    def unpack(path_in: str, path_out: str | None = None, key: str | bytes | None = None) -> None:
        Unpacker(path_in, path_out=path_out, key=key).unpack()

    @staticmethod
    def validate(path_in: str, key: str | bytes | None = None) -> None:
        Validator(path_in, key=key).validate()

    @staticmethod
    def print_version() -> None:
        logger.log(f"{PROJECT_NAME} {VERSION_STR} ({VERSION_INT})", Color.BLUE)
        release_date: str = RELEASE_DATE.strftime("%d.%m.%Y")
        logger.log(f"Released on {release_date}", Color.BLUE)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    operations: list[str] = ["pack", "unpack", "validate", "version"]
    parser.add_argument("operation", default="pack", type=str, choices=operations, help="Type of the operation")
    parser.add_argument("path", nargs="?", default=None, type=str, help="Path to the target file or folder")
    parser.add_argument("-o", default=None, type=str, required=False, help="Path to the output file or folder")
    parser.add_argument("-k", default=None, type=str, required=False, help="Path to the .key file or the "
                                                                           "key's hexadecimal value")
    args: argparse.Namespace = parser.parse_args()

    if args.operation == "version":
        Packman.print_version()
        return
    if args.path is None:
        logger.log(f"Path parameter was not provided", Color.RED)
        return

    match args.operation:
        case "pack":
            Packman.pack(args.path, path_out=args.o, key=args.k)
        case "unpack":
            Packman.unpack(args.path, path_out=args.o, key=args.k)
        case "validate":
            Packman.validate(args.path, key=args.k)


if __name__ == "__main__":
    main()
