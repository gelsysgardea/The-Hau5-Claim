from dataclasses import dataclass
from typing import Union


@dataclass
class Config:
    # ==================================================

    CHATS = [
        -1001610472708, 
        -1001813092752, 
        -1001515379979, 
        -1001644346269
    ]

    # ==================================================

    CLIENT_NAME: str = "ClientName"  # Client name | Can be left as now or changed
    API_ID: int = ...  # Telegram API ID
    API_HASH: str = ...  # Telegram API hash

    # ==================================================

    MAX_HOUR_REQUESTS: Union[int, float] = (
        100  # Maximum number of requests per hour (0 - unlimited)
    )

    headers = {
        "User-Agent": "",  # Constant value if logged in from one device
        "bnc-uuid": "",  # Constant value
        "device-info": "",  # Constant value if logged in from one device
        "clienttype": "web",  # Constant value
        "csrftoken": "",
        "fvideo-id": "", # Constant value
        "fvideo-token": "",
        "x-trace-id": "",
        "x-ui-request-trace": "",
        "lang": "uk-UA",  # Constant value
        "Referer": "https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox",  # Constant value
        "Cookie": '',
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)