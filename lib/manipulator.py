from datetime import datetime
from typing import List

import asyncio
import random

from lib import BinanceAPI
from source.config import Config
from source.utils import custom_print


class ManipulateToken:
    def __init__(self):
        self.api: BinanceAPI = BinanceAPI()
        self.config: Config = Config()

        self.last_timestamp = 0
        self.processed_tokens: List = []
        self.timeout: bool = False
        self.last_processed: bool = True

    async def main(self, token: str) -> None:
        timestamp = (
            datetime.now().replace(minute=0, second=0, microsecond=0).timestamp()
        )

        if timestamp > self.last_timestamp:
            self.processed_tokens.clear()
            self.last_processed = True
            self.timeout = False
            self.last_timestamp = timestamp

        if (token in self.processed_tokens) or (not self.last_processed):
            return

        if (
            len(self.processed_tokens) < self.config.MAX_HOUR_REQUESTS
            or self.config.MAX_HOUR_REQUESTS == 0
        ) and (not self.timeout):
            self.processed_tokens.append(token)
            self.last_processed = False

            custom_print(token, "info")

            await asyncio.sleep(random.randint(1, 5))
            result = await self.api.send_request(token)

            match result:
                case "captcha":
                    self.last_processed = False
                    self.timeout = True

                case "too_many_requests":
                    self.last_processed = False
                    self.timeout = True

                case "claimed" | "processed":
                    self.last_processed = True
                    self.processed_tokens.append(token)

        else:
            custom_print(
                f"{self.config.MAX_HOUR_REQUESTS} requests sent per hour. Sleeping for 1 hour.",
                "info",
            )
            self.timeout = True
            self.last_processed = False
            self.processed_tokens.clear()
