import hashlib
import io
import os
import pathlib
import time

from config import VERSION_INT, FORMAT_B, EXTENSION, BUFFER_SIZE
from encryption import encrypt_file, load_and_validate_key
from filesystem import list_folder, get_creation_timestamp
from logger import logger, Color
from validation import Validator


class Packer:

    def __init__(self, path_in: str, path_out: str | None = None, key: str | bytes | None = None) -> None:
        self.__path_in = os.path.abspath(path_in)
        self.__path_in_obj: pathlib.Path = pathlib.Path(self.__path_in)
        if path_out is None:
            path_out = os.path.join(os.getcwd(), f"{self.__path_in_obj.stem}.{EXTENSION}")
        self.__path_out: str = os.path.abspath(path_out)
        self.__key: bytes | None = load_and_validate_key(key)

    def __validate_before(self) -> bool:
        if self.__key is not None and len(self.__key) == 0:
            return False

        if not self.__path_in_obj.exists():
            return logger.log(f"Packing failed: input path must lead to an existing file or folder", Color.RED, False)

        if self.__path_out.lower() == self.__path_out.lower().removesuffix(f".{EXTENSION}"):
            return logger.log(f"Packing failed: output path must end with \".{EXTENSION}\"", Color.RED, False)

        return True


    def __pack_header(self, writer: io.BufferedWriter) -> None:
        version_and_flags: int = VERSION_INT * 2 + int(self.__key is not None)
        version_and_flags_b: bytes = version_and_flags.to_bytes(1)
        writer.write(FORMAT_B + version_and_flags_b)


    @staticmethod
    def __pack_file(path: str, writer: io.BufferedWriter, checksum: hashlib.sha3_256) -> None:
        size: int = os.path.getsize(path)
        size_b: bytes = size.to_bytes(8)
        writer.write(size_b)
        checksum.update(size_b)

        with open(path, "rb") as reader:
            while buffer := reader.read(BUFFER_SIZE):
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
            return 0  # File
        if path_obj.is_dir():
            return 1  # Folder
        return -1


    def __pack_item(self, path: str, writer: io.BufferedWriter) -> None:
        path_obj: pathlib.Path = pathlib.Path(path)
        checksum: hashlib.sha3_256 = hashlib.sha256()

        item_type: int = self.__get_item_type(path_obj)
        if item_type < 0:
            logger.log(f"Unable to pack \"{path}\"", Color.RED)
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
            percentage: float = index / len(items)
            logger.log(f"Packing {percentage:.1%} \"{path}\"...")
            self.__pack_item(path, writer)


    def pack(self) -> None:
        start_time: float = time.time()

        if not self.__validate_before():
            return

        with open(self.__path_out, "wb") as writer:
            self.__pack_header(writer)
            self.__pack_items(writer)

        if self.__key is not None:
            logger.log(f"Encrypting \"{self.__path_out}\"...")
            encrypted_output_path: str = f"{self.__path_out[:-4]}.encrypted.{self.__path_out[-3:]}"

            with open(self.__path_out, "rb") as reader, open(encrypted_output_path, "wb") as writer:
                header: bytes = reader.read(5)
                writer.write(header)
                encrypt_file(reader, writer, self.__key)

            os.remove(self.__path_out)
            os.rename(encrypted_output_path, self.__path_out)

        if not Validator(self.__path_out, key=self.__key).validate():
            return

        end_time: float = time.time()
        time_difference: float = end_time - start_time
        logger.log(f"Packing complete ({time_difference:.3f}s)", Color.GREEN)
