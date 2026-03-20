from datetime import date


# Project
PROJECT_NAME: str = "Packman"
VERSION_STR: str = "v1.3.0"
VERSION_INT: int = 3
RELEASE_DATE: date = date(day=20, month=3, year=2026)

# Format
FORMAT_B: bytes = b".PKD"  # exactly 4 bytes long
EXTENSION: str = "pkd"
KEY_EXTENSION: str = "key"

# Logger
LOG: bool = True
ANSI_COLORS: bool = True

# Performance
BUFFER_SIZE: int = 16 * 1024 * 1024  # in bytes
