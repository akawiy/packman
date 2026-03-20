import hashlib
import io
import os
import pathlib

from config import PROJECT_NAME, VERSION_INT, FORMAT_B, EXTENSION, BUFFER_SIZE
from encryption import decrypt_file, load_and_validate_key
from logger import logger, Color


class Validator:

    def __init__(self, path_in: str, key: str | bytes | None = None) -> None:
        self.__path_in: str = os.path.abspath(path_in)
        self.__key: bytes | None = load_and_validate_key(key)

        self.__item_count: int | None = None
        self.__is_encrypted: bool | None = None


    @property
    def item_count(self) -> int | None:
        return self.__item_count

    @property
    def is_encrypted(self) -> bool | None:
        return self.__is_encrypted


    def __validate_before(self) -> bool:
        if self.__path_in.lower() == self.__path_in.lower().removesuffix(f".{EXTENSION}"):
            return logger.log(f"Validation failed: input path must end with \".{EXTENSION}\"", Color.RED, False)

        path_in_obj: pathlib.Path = pathlib.Path(self.__path_in)
        if not path_in_obj.exists() or not path_in_obj.is_file():
            return logger.log(f"Validation failed: input path must lead to an existing file", Color.RED, False)

        return True


    @staticmethod
    def __insufficient_content_size() -> bool:
        return logger.log("Validation failed: insufficient content size", Color.RED, False)


    def __validate_header(self, reader: io.BufferedReader) -> bool:
        format_b: bytes = reader.read(4)
        if len(format_b) < 4:
            return self.__insufficient_content_size()

        version_and_flags_b: bytes = reader.read(1)
        if len(version_and_flags_b) < 1:
            return self.__insufficient_content_size()
        version_and_flags: int = int.from_bytes(version_and_flags_b)

        version: int = version_and_flags // 2
        self.__is_encrypted: bool = bool(version_and_flags % 2)

        if version != VERSION_INT:
            if not logger.confirm(f"Warning: {PROJECT_NAME} version ({VERSION_INT}) does not match the file "
                                  f"version ({version}), which may cause unexpected behaviour during validation "
                                  f"and unpacking. Do you want to continue?", Color.YELLOW):
                return False

        if format_b != FORMAT_B:
            return logger.log(f"Validation failed: incorrect file format provided", Color.RED, False)

        return True


    def __validate_file(self, reader: io.BufferedReader, checksum: hashlib.sha3_256) -> bool:
        size_b: bytes = reader.read(8)
        if len(size_b) < 8:
            return self.__insufficient_content_size()
        size: int = int.from_bytes(size_b)
        checksum.update(size_b)

        while size > 0:
            buffer_size: int = min(size, BUFFER_SIZE)
            buffer: bytes = reader.read(buffer_size)
            if len(buffer) < buffer_size:
                return self.__insufficient_content_size()
            size -= buffer_size
            checksum.update(buffer)

        return True


    def __validate_folder(self, reader: io.BufferedReader, checksum: hashlib.sha3_256, location: list[int]) -> bool:
        folder_item_count_b: bytes = reader.read(4)
        if len(folder_item_count_b) < 4:
            return self.__insufficient_content_size()
        folder_item_count: int = int.from_bytes(folder_item_count_b)
        checksum.update(folder_item_count_b)
        location.append(folder_item_count)

        return True


    def __validate_item(self, reader: io.BufferedReader, location: list[int]) -> bool | None:
        checksum: hashlib.sha3_256 = hashlib.sha256()

        item_type_b: bytes = reader.read(1)
        if len(item_type_b) == 0:
            return None
        item_type: int = int.from_bytes(item_type_b)

        item_name_size_b: bytes = reader.read(1)
        if len(item_name_size_b) < 1:
            return self.__insufficient_content_size()
        item_name_size: int = int.from_bytes(item_name_size_b)

        item_name_b: bytes = reader.read(item_name_size)
        if len(item_name_b) < item_name_size:
            return self.__insufficient_content_size()

        creation_timestamp_b: bytes = reader.read(8)
        if len(creation_timestamp_b) < 8:
            return self.__insufficient_content_size()

        modification_timestamp_b: bytes = reader.read(8)
        if len(modification_timestamp_b) < 8:
            return self.__insufficient_content_size()

        all_b: bytes = item_type_b + item_name_size_b + item_name_b + creation_timestamp_b + modification_timestamp_b
        checksum.update(all_b)

        match item_type:
            case 0:  # File
                if not self.__validate_file(reader, checksum):
                    return False
            case 1:  # Folder
                if not self.__validate_folder(reader, checksum, location):
                    return False

        stored_checksum: bytes = reader.read(32)
        if len(stored_checksum) < 32:
            return self.__insufficient_content_size()
        if checksum.digest() != stored_checksum:
            return logger.log("Validation failed: checksums did not match", Color.RED, False)
        return True


    def __validate_items(self, reader: io.BufferedReader) -> bool:
        location: list[int] = []
        self.__item_count: int = 0

        while True:
            if len(location) > 0:
                location[-1] -= 1

            item_result: bool | None = self.__validate_item(reader, location)
            if item_result is None:
                break
            self.__item_count += 1
            if not item_result:
                return False

            while len(location) > 0 and location[-1] == 0:
                location.pop()

        if len(location) > 0:
            return logger.log("Validation failed: file tree is incorrect", Color.RED, False)
        return True


    def validate(self) -> bool:
        logger.log(f"Validating \"{self.__path_in}\"...")
        if not self.__validate_before():
            return False

        encrypted_output_path: str = f"{self.__path_in[:-4]}.encrypted.{self.__path_in[-3:]}"
        if self.__key is not None:
            logger.log(f"Decrypting \"{self.__path_in}\"...")
            os.rename(self.__path_in, encrypted_output_path)

            with open(encrypted_output_path, "rb") as reader, open(self.__path_in, "wb") as writer:
                header: bytes = reader.read(5)
                writer.write(header)
                decrypt_file(reader, writer, self.__key)

        with open(self.__path_in, "rb") as reader:
            if not self.__validate_header(reader):
                return False
            if not self.__validate_items(reader):
                return False

        if self.__key is not None:
            os.remove(self.__path_in)
            os.rename(encrypted_output_path, self.__path_in)

        return logger.log("Validation successful", Color.GREEN, True)
