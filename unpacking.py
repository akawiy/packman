import io
import os
import pathlib
import platform
import time
import win32_setctime

from config import BUFFER_SIZE
from encryption import decrypt_file, load_and_validate_key
from logger import logger, Color
from validation import Validator


class Unpacker:

    def __init__(self, path_in: str, path_out: str | None = None, key: str | bytes | None = None) -> None:
        self.__path_in: str = os.path.abspath(path_in)
        self.__path_out: str | None = path_out and os.path.abspath(path_out)
        self.__key: bytes | None = load_and_validate_key(key)

        self.__timestamps: list[tuple[str, int, int]] = []


    def __get_path(self, item_name: str, location: list[list[str | int]], index: int) -> str:
        if self.__path_out is None:
            return os.path.join(os.getcwd(), *[i[0] for i in location], item_name)
        if index == 0:
            return self.__path_out
        return os.path.join(self.__path_out, *[i[0] for i in location[1:]], item_name)


    @staticmethod
    def __unpack_file(reader: io.BufferedReader, file_path: str) -> None:
        size_b: bytes = reader.read(8)
        size: int = int.from_bytes(size_b)

        with open(file_path, "wb") as writer:
            while size > 0:
                buffer_size: int = min(size, BUFFER_SIZE)
                buffer: bytes = reader.read(buffer_size)
                size -= buffer_size
                writer.write(buffer)


    @staticmethod
    def __unpack_folder(reader: io.BufferedReader, folder_path: str, location: list[list[str | int]]) -> None:
        folder_item_count_b: bytes = reader.read(4)
        folder_item_count: int = int.from_bytes(folder_item_count_b)
        folder_path_obj: pathlib.Path = pathlib.Path(folder_path)
        location.append([folder_path_obj.name, folder_item_count])
        folder_path_obj.mkdir(exist_ok=True)  # Will throw an error it one of the parent folders don't exist


    def __unpack_item(
            self,
            reader: io.BufferedReader,
            location: list[list[str | int]],
            item_count: int,
            item_index: int,
    ) -> bool:
        item_type_b: bytes = reader.read(1)
        if len(item_type_b) == 0:
            return False  # No more items to unpack
        item_type: int = int.from_bytes(item_type_b)

        item_name_size_b: bytes = reader.read(1)
        item_name_size: int = int.from_bytes(item_name_size_b)

        item_name_b: bytes = reader.read(item_name_size)
        item_name: str = item_name_b.decode()

        item_path: str = self.__get_path(item_name, location, item_index)
        percentage: float = item_index / item_count
        logger.log(f"Unpacking {percentage:.1%} \"{item_path}\"...")

        creation_timestamp_b: bytes = reader.read(8)
        creation_timestamp: int = int.from_bytes(creation_timestamp_b)

        modification_timestamp_b: bytes = reader.read(8)
        modification_timestamp: int = int.from_bytes(modification_timestamp_b)

        if self.__path_out is None or item_index != 0:
            self.__timestamps.append((item_path, creation_timestamp, modification_timestamp))

        match item_type:
            case 0:
                self.__unpack_file(reader, item_path)
            case 1:
                self.__unpack_folder(reader, item_path, location)

        reader.read(32)  # Ignoring checksum as it has already been checked by the validator
        return True


    def __unpack_items(self, reader: io.BufferedReader, item_count: int) -> None:
        location: list[list[str | int]] = []
        item_index: int = 0

        while True:
            if len(location) > 0:
                location[-1][1] -= 1

            if not self.__unpack_item(reader, location, item_count, item_index):
                break
            item_index += 1

            while len(location) > 0 and location[-1][1] == 0:
                location.pop()

        logger.log("Setting timestamps...")
        for item_path, creation_timestamp, modification_timestamp in self.__timestamps:
            if platform.system() == "Windows":
                win32_setctime.setctime(item_path, creation_timestamp)
            os.utime(item_path, (time.time(), modification_timestamp))


    def unpack(self) -> None:
        start_time: float = time.time()
        self.__timestamps.clear()

        validator: Validator = Validator(self.__path_in, key=self.__key)
        if not validator.validate():
            return

        encrypted_output_path: str = f"{self.__path_in[:-4]}.encrypted.{self.__path_in[-3:]}"
        if self.__key is not None:
            logger.log(f"Decrypting \"{self.__path_in}\"...")
            os.rename(self.__path_in, encrypted_output_path)

            with open(encrypted_output_path, "rb") as reader, open(self.__path_in, "wb") as writer:
                header: bytes = reader.read(5)
                writer.write(header)
                decrypt_file(reader, writer, self.__key)

        with open(self.__path_in, "rb") as reader:
            reader.read(5)  # Ignoring format, version and flags as they have already been checked by the validator
            self.__unpack_items(reader, validator.item_count)

        if self.__key is not None:
            os.remove(self.__path_in)
            os.rename(encrypted_output_path, self.__path_in)

        end_time: float = time.time()
        time_difference: float = end_time - start_time
        logger.log(f"Unpacking complete ({time_difference:.3f}s)", Color.GREEN)
