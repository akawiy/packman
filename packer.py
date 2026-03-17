import hashlib
import io
import os
import pathlib
import time

from config import VERSION_INT, MAGIC, EXTENSION, RAM_BUFFER_SIZE
from misc import colored, list_folder, get_creation_timestamp
from validator import Validator


class Packer:

    def __init__(self, path_in: str, path_out: str | None = None, log_details: bool = False) -> None:
        self.__path_in = os.path.abspath(path_in)
        self.__path_in_obj: pathlib.Path = pathlib.Path(self.__path_in)
        if path_out is None:
            path_out = os.path.join(os.getcwd(), f"{self.__path_in_obj.stem}.{EXTENSION}")
        self.__path_out: str = os.path.abspath(path_out)
        self.__log_details: bool = log_details


    def __validate_before(self) -> bool:
        if not self.__path_in_obj.exists():
            if self.__log_details:
                print(colored(f"Packing failed: input path must lead to an existing file or folder", 31))
            return False

        if self.__path_out == self.__path_out.removesuffix(f".{EXTENSION}"):
            if self.__log_details:
                print(colored(f"Packing failed: output path must end with \".{EXTENSION}\"", 31))
            return False

        return True


    @staticmethod
    def __pack_file(path: str, writer: io.BufferedWriter, checksum: hashlib.sha3_256) -> None:
        size: int = os.path.getsize(path)
        size_b: bytes = size.to_bytes(8)
        writer.write(size_b)
        checksum.update(size_b)

        with open(path, "rb") as reader:
            while buffer := reader.read(RAM_BUFFER_SIZE):
                writer.write(buffer)
                checksum.update(buffer)


    @staticmethod
    def __pack_folder(path: str, writer: io.BufferedWriter, checksum: hashlib.sha3_256) -> None:
        folder_item_count: int = len(os.listdir(path))
        folder_item_count_b: bytes = folder_item_count.to_bytes(4)
        writer.write(folder_item_count_b)
        checksum.update(folder_item_count_b)


    @staticmethod
    def __get_item_type(path_obj: pathlib.Path) -> int:
        if path_obj.is_file():
            return 0
        if path_obj.is_dir():
            return 1
        return -1


    def __pack_item(self, path: str, writer: io.BufferedWriter) -> None:
        path_obj: pathlib.Path = pathlib.Path(path)
        checksum: hashlib.sha3_256 = hashlib.sha256()

        item_type: int = self.__get_item_type(path_obj)
        if item_type < 0:
            self.__log_unable_to_pack(path)
            return
        item_type_b: bytes = item_type.to_bytes(1)
        item_name: str = path_obj.name
        item_name_b: bytes = item_name.encode()
        item_name_size: int = len(item_name_b)
        item_name_size_b: bytes = item_name_size.to_bytes(1)
        creation_timestamp: int = int(get_creation_timestamp(path))
        creation_timestamp_b: bytes = creation_timestamp.to_bytes(8)
        modification_timestamp: int = int(os.path.getmtime(path))
        modification_timestamp_b: bytes = modification_timestamp.to_bytes(8)
        all_b: bytes = item_type_b + item_name_size_b + item_name_b + creation_timestamp_b + modification_timestamp_b
        writer.write(all_b)
        checksum.update(all_b)

        match item_type:
            case 0:
                self.__pack_file(path, writer, checksum)
            case 1:
                self.__pack_folder(path, writer, checksum)

        writer.write(checksum.digest())


    def __pack_items(self, writer: io.BufferedWriter) -> None:
        items: list[str] = [self.__path_in] + list_folder(self.__path_in)

        for index, path in enumerate(items):
            self.__log_packing(items, index, path)
            self.__pack_item(path, writer)


    def __log_packing(self, items: list[str], index: int, path: str) -> None:
        if not self.__log_details:
            return

        percentage: float = index / len(items)
        print(f"Packing {percentage:.1%} \"{path}\"...")


    def __log_unable_to_pack(self, path: str) -> None:
        if not self.__log_details:
            return

        print(colored(f"Unable to pack \"{path}\"", 33))


    def __log_done(self, start_time: float) -> None:
        if not self.__log_details:
            return

        end_time: float = time.time()
        time_difference: float = end_time - start_time
        print(colored(f"Packing complete ({time_difference:.3f}s)", 32))


    def pack(self) -> None:
        if not self.__validate_before():
            return
        start_time: float = time.time()

        with open(self.__path_out, "wb") as writer:
            writer.write(MAGIC + VERSION_INT.to_bytes(1))
            self.__pack_items(writer)

        if not Validator(self.__path_out, log_details=self.__log_details).validate():
            return
        self.__log_done(start_time)
