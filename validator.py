import hashlib
import io
import os
import pathlib

from config import PROJECT_NAME, VERSION_INT, MAGIC, EXTENSION, RAM_BUFFER_SIZE
from misc import colored


class Validator:

    def __init__(self, path_in: str, log_details: bool = False) -> None:
        self.__path_in: str = os.path.abspath(path_in)
        self.__log_details: bool = log_details

        self.__item_count: int | None = None


    @property
    def item_count(self) -> int | None:
        return self.__item_count


    def __validate_before(self) -> bool:
        path_in_obj: pathlib.Path = pathlib.Path(self.__path_in)
        if self.__path_in == self.__path_in.removesuffix(f".{EXTENSION}"):
            if self.__log_details:
                print(colored(f"Validation failed: input path must end with \".{EXTENSION}\"", 31))
            return False
        if not path_in_obj.exists() or not path_in_obj.is_file():
            if self.__log_details:
                print(colored(f"Validation failed: input path must lead to an existing file", 31))
            return False

        return True


    def __validate_magic(self, reader: io.BufferedReader) -> bool:
        magic_b: bytes = reader.read(4)

        if magic_b == MAGIC:
            return True
        if self.__log_details:
            print(colored("Validation failed: magic is incorrect, this potentially "
                          "means file of the wrong format is being provided", 31))
        return False


    def __validate_version(self, reader: io.BufferedReader) -> bool:
        version_b: bytes = reader.read(1)
        version: int = int.from_bytes(version_b)

        if version == VERSION_INT:
            return True
        if self.__log_details:
            while (i := input(colored(
                    f"Warning: {PROJECT_NAME} version ({VERSION_INT}) does not match the file "
                    f"version ({version}), which may cause unexpected behaviour during validation "
                    f"and unpacking. Do you want to continue? [Y / N]: ", 33
            ))) not in ["Y", "N"]:
                pass
            if i == "N":
                return False
        return True


    def __validate_file(self, reader: io.BufferedReader, checksum: hashlib.sha3_256) -> bool:
        size_b: bytes = reader.read(8)
        if len(size_b) < 8:
            return self.__insufficient_content_size()
        size: int = int.from_bytes(size_b)
        checksum.update(size_b)

        while size > 0:
            buffer_size: int = min(size, RAM_BUFFER_SIZE)
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
            case 0:
                if not self.__validate_file(reader, checksum):
                    return False
            case 1:
                if not self.__validate_folder(reader, checksum, location):
                    return False

        if checksum.digest() != reader.read(32):
            return self.__checksums_did_not_match()
        return True


    def __validate_items(self, reader: io.BufferedReader) -> bool:
        location: list[int] = []
        self.__item_count: int = 0

        while True:
            if len(location) > 0:
                location[-1] -= 1

                if location[-1] == 0:
                    location.pop()

            item_result: bool | None = self.__validate_item(reader, location)
            if item_result is None:
                break
            self.__item_count += 1
            if not item_result:
                return False

        if len(location) > 0:
            return self.__file_tree_incorrect()
        return True


    def __log_validating(self) -> None:
        if not self.__log_details:
            return
        print(f"Validating \"{self.__path_in}\"...")


    def __insufficient_content_size(self) -> bool:
        if self.__log_details:
            print(colored("Validation failed: insufficient content size", 31))
        return False


    def __checksums_did_not_match(self) -> bool:
        if self.__log_details:
            print(colored("Validation failed: checksums did not match", 31))
        return False


    def __file_tree_incorrect(self) -> bool:
        if self.__log_details:
            print(colored("Validation failed: file tree is incorrect", 31))
        return False


    def __success(self) -> bool:
        if self.__log_details:
            print(colored("Validation successful", 32))
        return True


    def validate(self) -> bool:
        self.__log_validating()
        if not self.__validate_before():
            return False

        with open(self.__path_in, "rb") as reader:
            if not self.__validate_magic(reader):
                return False
            if not self.__validate_version(reader):
                return False
            if not self.__validate_items(reader):
                return False

        return self.__success()
