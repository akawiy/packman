import argparse

from config import PROJECT_NAME, VERSION_STR, VERSION_INT, RELEASE_DATE
from misc import colored
from packer import Packer
from unpacker import Unpacker
from validator import Validator


def print_version() -> None:
    print(colored(f"{PROJECT_NAME} {VERSION_STR} ({VERSION_INT})", 34))
    release_date: str = RELEASE_DATE.strftime("%d.%m.%Y")
    print(colored(f"Released on {release_date}", 34))


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        default="pack",
        type=str,
        choices=["pack", "unpack", "validate", "version"],
        help="Type of the operation",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        type=str,
        help="Path to the target file or folder",
    )
    parser.add_argument(
        "-o",
        default=None,
        type=str,
        required=False,
        help="Path to the output file or folder",
    )
    args: argparse.Namespace = parser.parse_args()

    if args.operation == "version":
        print_version()
        return
    if args.path is None:
        print(colored(f"Path parameter was not provided", 31))
        return

    match args.operation:
        case "pack":
            Packer(args.path, path_out=args.o, log_details=True).pack()
        case "unpack":
            Unpacker(args.path, path_out=args.o, log_details=True).unpack()
        case "validate":
            Validator(args.path, log_details=True).validate()


if __name__ == "__main__":
    main()
