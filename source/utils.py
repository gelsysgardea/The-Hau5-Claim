from typing import Literal


def custom_print(
    text: str,
    suffix: Literal["info", "error", "warn"] = "info",
) -> None:
    
    suffixes = {
        "info": "\033[1;32;48mINFO\033[1;37;0m",
        "error": "\033[1;31;48mERROR\033[1;37;0m",
        "warn": "\033[1;33mWARN\033[1;37;0m",
    }

    print(f"[{suffixes[suffix]}]: {text}")
    return

