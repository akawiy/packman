import io
import pathlib

from config import KEY_EXTENSION, BUFFER_SIZE
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from logger import logger, Color


def encrypt_file(reader: io.BufferedReader, writer: io.BufferedWriter, key: bytes) -> None:
    base_nonce: bytes = get_random_bytes(12)
    counter: int = 0
    writer.write(base_nonce)

    while True:
        data_chunk: bytes = reader.read(BUFFER_SIZE)
        if len(data_chunk) == 0:
            break

        counter_b: bytes = counter.to_bytes(4)
        nonce: bytes = base_nonce[:8] + counter_b
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        encrypted_data, tag = cipher.encrypt_and_digest(data_chunk)
        encrypted_chunk: bytes = encrypted_data + tag
        encrypted_chunk_size: int = len(encrypted_chunk)
        encrypted_chunk_size_b: bytes = encrypted_chunk_size.to_bytes(4)
        writer.write(encrypted_chunk_size_b + encrypted_chunk)
        counter += 1


def decrypt_file(reader: io.BufferedReader, writer: io.BufferedWriter, key: bytes) -> None:
    base_nonce: bytes = reader.read(12)
    counter: int = 0

    while True:
        encrypted_chunk_size_b: bytes = reader.read(4)
        if len(encrypted_chunk_size_b) == 0:
            break
        encrypted_chunk_size: int = int.from_bytes(encrypted_chunk_size_b)
        encrypted_chunk = reader.read(encrypted_chunk_size)
        encrypted_data: bytes = encrypted_chunk[:-16]
        tag: bytes = encrypted_chunk[-16:]
        counter_b: bytes = counter.to_bytes(4)
        nonce: bytes = base_nonce[:8] + counter_b
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        data_chunk: bytes = cipher.decrypt_and_verify(encrypted_data, tag)
        writer.write(data_chunk)
        counter += 1


def load_and_validate_key(path_or_hex_or_bytes: str | bytes | None) -> bytes | None:
    incorrect_size: str = "Incorrect key size: key should be 32 bytes long"

    if path_or_hex_or_bytes is None:
        return None

    if type(path_or_hex_or_bytes) is bytes:
        key_b: bytes = path_or_hex_or_bytes

        if len(key_b) != 32:
            return logger.log(incorrect_size, Color.RED, b"")
        return key_b

    path_or_hex: str = path_or_hex_or_bytes
    try:
        key_b: bytes = bytes.fromhex(path_or_hex)
    except ValueError:
        pass
    else:
        if len(key_b) != 32:
            return logger.log(incorrect_size, Color.RED, b"")
        return key_b

    path: str = path_or_hex
    if path.lower() == path.lower().removesuffix(f".{KEY_EXTENSION}"):
        return logger.log(f"Key loading failed: path must end with \".{KEY_EXTENSION}\"", Color.RED, b"")

    path_obj: pathlib.Path = pathlib.Path(path)
    if not path_obj.exists():
        logger.log("Key loading failed: path must lead to an existing file", Color.RED)

    with open(path, "r") as file:
        key_hex: str = file.read(64).strip()

    try:
        key_b: bytes = bytes.fromhex(key_hex)
    except ValueError:
        return logger.log("Incorrect key format: key should be represented as a 64-digit hexadecimal", Color.RESET, b"")
    else:
        if len(key_b) != 32:
            return logger.log(incorrect_size, Color.RED, b"")
        return key_b
