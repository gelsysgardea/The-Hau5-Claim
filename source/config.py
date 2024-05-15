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
    API_ID: int = 21983845  # Telegram API ID
    API_HASH: str = "***REMOVED***"  # Telegram API hash

    # ==================================================

    MAX_HOUR_REQUESTS: Union[int, float] = (
        100  # Maximum number of requests per hour (0 - unlimited)
    )

    # headers = {
    #     "User-Agent": "",  # Constant value if logged in from one device
    #     "bnc-uuid": "",  # Constant value
    #     "device-info": "",  # Constant value if logged in from one device
    #     "clienttype": "web",  # Constant value
    #     "csrftoken": "",
    #     "fvideo-id": "", # Constant value
    #     "fvideo-token": "",
    #     "x-trace-id": "",
    #     "x-ui-request-trace": "",
    #     "lang": "uk-UA",  # Constant value
    #     "Referer": "https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox",  # Constant value
    #     "Cookie": "",
    # }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "bnc-uuid": "***REMOVED***",
        "device-info": "***REMOVED***",
        "clienttype": "web",
        "csrftoken": "***REMOVED***",
        "fvideo-id": "***REMOVED***",
        "fvideo-token": "***REMOVED***",
        "x-trace-id": "***REMOVED***",
        "x-ui-request-trace": "***REMOVED***",
        "lang": "uk-UA",
        "Referer": "https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox",
        "Cookie": 'theme=dark; bnc-uuid=***REMOVED***; source=Homepage_log_in; campaign=duckduckgo.com; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22496344464%22%2C%22first_id%22%3A%2218de07474ed694-0311e8d2b3183b-e565623-2073600-18de07474ee600%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C…055717020c0ace63170ad5f6066813":{"date":1710514143189,"value":""}}; _ga_3WP50LGEEC=GS1.1.1708976615.6.1.1708978039.60.0.0; _ga=GA1.1.2117806244.1708883765; changeBasisTimeZone=; lang=uk-ua; se_sd=RJSBQQR5bRaUVICoLEhZgZZCwHRQHEVUlcSBdV0d1RSUgWlNWUJc1; cr00=529D8EBD8E8200C5DDF6D173AB3893B0; d1og=web.496344464.5EB82DB8FB781D69B2A36AAF8BC87282; r2o1=web.496344464.3D251940C1F2EAAC401245A1CC265833; f30l=web.496344464.A1A3B090E3D38945C213F51FF652665D; logined=y; p20t=web.496344464.C110552A84DF73235BB6E2530FA27A21',
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
