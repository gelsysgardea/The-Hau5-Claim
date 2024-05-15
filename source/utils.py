import datetime

from typing import Literal


def custom_print(
    text: str,
    suffix: Literal["success", "error", "info"] = "success",
) -> None:

    date = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "]"
    suffixes = {
        "success": "\033[1;32;48mSUCCESS\033[1;37;0m",
        "error": "\033[1;31;48mERROR\033[1;37;0m",
        "info": "\033[1;33mINFO\033[1;37;0m",
    }

    print(f"{date} {suffixes[suffix]}: {text}")
    return

