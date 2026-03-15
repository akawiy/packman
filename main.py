import os
import argparse

from config import ARGUMENT_DESCRIPTIONS
from pack import pack
from unpack import unpack
from validate import validate


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        default="pack",
        type=str,
        choices=["pack", "unpack", "validate"],
        help=ARGUMENT_DESCRIPTIONS["operation"],
    )
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

    match args.operation:
        case "pack":
            pack(args.path, path_out=args.o, log_details=True)
        case "unpack":
            unpack(args.path, path_out=args.o, log_details=True)
        case "validate":
            validate(args.path, log_details=True)


if __name__ == "__main__":
    main()
