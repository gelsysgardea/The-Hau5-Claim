import re
from typing import Optional

import aiohttp

from source import Config
from source import custom_print


class BinanceAPI:
    def __init__(self):
        self.config: Config = Config()
        self.response: Optional[aiohttp.ClientResponse]

    async def send_request(self, redpacket: str) -> Optional[str]:
        """
        Send request to Binance API and return response
        :param redpacket: Redpacket ID
        :return: string or None
        """

        async with aiohttp.ClientSession(headers=self.config.headers) as session:
            try:
                self.response = await session.post(
                    "https://www.binance.com/bapi/pay/v1/private/binance-pay/gift-box/code/grabV2",
                    json={"channel": "DEFAULT", "grabCode": redpacket, "scene": None},
                )
            except (
                aiohttp.ClientConnectorError,
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientError,
                aiohttp.ClientTimeout,
                aiohttp.ServerTimeoutError,
            ):
                custom_print(
                    "An error occurred, while connecting to Binance API", "error"
                )
                return "processed"

        response_json = await self.response.json()
        if response_json["success"]:
            print(f">> [Currency]: {response_json['data']['currency']}")
            print(f">> [Amount]: {response_json['data']['grabAmountStr']}")
            return "claimed"

        elif response_json.get("data", None) and "validateId" in response_json["data"]:
            custom_print(
                f"Captcha. Break time for 1 hour."
                f"({match.group(1)} hours)",
                "error",
            )
            return "captcha"

        match response_json["code"]:
            case "100002001":
                custom_print("Session expired. Re-enter new credintials", "error")
            case "403067":
                match = re.search(r"через (\d+:\d+)", response_json["message"])
                custom_print(
                    f"Too many requests. Break time for 1 hour."
                    f"({match.group(1)} hours)",
                    "error",
                )
                return "too_many_requests"

            case "403802":
                custom_print(f"{redpacket} Crypto Box has been claimed", "error")
                return "processed"

            case "PAY4001COM000" | "403803":
                custom_print(f"Invalid redpacket entered: {redpacket}", "info")
                return "processed"
