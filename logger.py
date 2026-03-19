from config import LOG, ANSI_COLORS
from enum import Enum
from typing import Any


class Color(Enum):

    RESET  = 0
    RED    = 31
    GREEN  = 32
    YELLOW = 33
    BLUE   = 34


class Logger:

    def __init__(self, enabled: bool = True, ansi_colors: bool = True) -> None:
        self.__enabled: bool = enabled
        self.__ansi_colors: bool = ansi_colors


    @property
    def enabled(self) -> bool:
        return self.__enabled

    def enable(self) -> None:
        self.__enabled = True

    def disable(self) -> None:
        self.__enabled = False


    @property
    def ansi_colors(self) -> bool:
        return self.__ansi_colors


    def log(self, text: str, color_code: Color = Color.RESET, return_value: Any = None) -> Any:
        if self.__enabled:
            if self.__ansi_colors:
                text = f"\033[{color_code.value}m{text}\033[{color_code.RESET.value}m"
            print(text)
        return return_value

    def ask(self, prompt: str, color_code: Color = Color.RESET) -> str:
        if self.__ansi_colors:
            prompt = f"\033[{color_code.value}m{prompt}\033[{color_code.RESET.value}m"
        if not self.__enabled:
            prompt = ""
        return input(prompt)

    def confirm(self, action: str, color_code: Color = Color.RESET) -> bool:
        if not self.__enabled:
            return True
        options: list[str] = ["y", "n"]
        while (i := self.ask(f"{action} [{' / '.join(options)}]: ", color_code)) not in options:
            pass
        return not bool(options.index(i))

logger: Logger = Logger(LOG, ANSI_COLORS)
