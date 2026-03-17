from datetime import date


PROJECT_NAME: str = "Packman"
VERSION_STR: str = "v1.2.0"
VERSION_INT: int = 2
RELEASE_DATE: date = date(day=17, month=3, year=2026)
MAGIC: bytes = b"PKMN"  # 4 bytes long
EXTENSION: str = "pkd"
ANSI_COLORS: bool = True
RAM_BUFFER_SIZE: int = 65_536  # in bytes
