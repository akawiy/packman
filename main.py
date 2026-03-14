import os
import pathlib
import argparse


def pack(
        path_in: str,
        path_out: str | None = None,
        log: bool = False,
        rewrite: bool = True,
        extension: str = "pkd",  # Previously .sec
) -> None:
    if log:
        print(f"Packing \"{path_in}\"")

    path_in = os.path.abspath(path_in)
    path_in_obj: pathlib.Path = pathlib.Path(path_in)
    if path_out is None:
        path_out = os.path.join(os.getcwd(), f"{path_in_obj.stem}.{extension}")
    path_out = os.path.abspath(path_out)
    if rewrite:
        open(path_out, "wb").close()

    item_name: bytes = path_in_obj.name.encode("UTF-8")
    item_name_length: bytes = len(item_name).to_bytes(1)
    with open(path_out, "ab") as file:
        # noinspection PyTypeChecker
        file.write(item_name_length)
        # noinspection PyTypeChecker
        file.write(item_name)

    if path_in_obj.is_dir():
        folder_item_count: bytes = len(os.listdir(path_in)).to_bytes(4)
        with open(path_out, "ab") as file:
            # noinspection PyTypeChecker
            file.write(folder_item_count)

        folders: list[str] = []
        files: list[str] = []

        for subitem_name in os.listdir(path_in):
            subitem_path: str = os.path.join(path_in, subitem_name)
            subitem_path_obj: pathlib.Path = pathlib.Path(subitem_path)

            if subitem_path_obj.is_dir():
                folders.append(subitem_path)
            elif subitem_path_obj.is_file():
                files.append(subitem_path)

        for subitem_path in folders + files:
            pack(subitem_path, path_out=path_out, log=log, rewrite=False, extension=extension)
    elif path_in_obj.is_file():
        with open(path_in, "rb") as file:
            file_content: bytes = file.read()
        file_content_size: bytes = len(file_content).to_bytes(8)

        with open(path_out, "ab") as file:
            # noinspection PyTypeChecker
            file.write(file_content_size)
            # noinspection PyTypeChecker
            file.write(file_content)


def unpack(path_in: str, path_out: str | None = None, log: bool = False) -> None:
    path_in = os.path.abspath(path_in)
    if path_out is None:
        path_out = os.getcwd()
    path_out = os.path.abspath(path_out)

    content: bytes = b""
    with open(path_in, "rb") as file:
        content: bytes = file.read()

    location: dict[str, int] = {}
    while content:
        item_name_length: int = int.from_bytes(content[:1])
        content = content[1:]
        item_name: str = content[:item_name_length].decode("UTF-8")
        content = content[item_name_length:]
        item_path: str = os.path.join(path_out, *location.keys(), item_name)
        item_path_obj: pathlib.Path = pathlib.Path(item_path)
        if log:
            print(f"Unpacking \"{item_path}\"")

        if len(location) > 0:
            parent_folder_name: str = list(location.keys())[-1]
            location[parent_folder_name] -= 1

            if location[parent_folder_name] == 0:
                del location[parent_folder_name]

        if "." not in item_name:
            folder_item_count: int = int.from_bytes(content[:4])
            content = content[4:]
            location[item_name] = folder_item_count
            item_path_obj.mkdir(parents=True, exist_ok=True)
        else:
            file_content_size: int = int.from_bytes(content[:8])
            content = content[8:]
            file_content: bytes = content[:file_content_size]
            content = content[file_content_size:]

            with open(item_path, "wb") as file:
                # noinspection PyTypeChecker
                file.write(file_content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        default="pack",
        type=str,
        choices=["pack", "unpack"],
        help="Type of the operation",
    )
    parser.add_argument(
        "path",
        default=os.getcwd(),
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

    match args.operation:
        case "pack":
            pack(args.path, args.o, log=True)
        case "unpack":
            unpack(args.path, args.o, log=True)


if __name__ == "__main__":
    main()
