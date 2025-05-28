from dataclasses import dataclass
from typing import Union


@dataclass
class Config:
    # ==================================================

    # Lista de chats a monitorear (se llenará dinámicamente)
    CHATS = []
    
    # Patrón para excluir chats que contengan 'intel' (case insensitive)
    EXCLUDE_CHATS_WITH = ['intel']

    # ==================================================

    # ==================================================
    # CONFIGURACIÓN DE LA API DE TELEGRAM
    # Obtén estos valores en https://my.telegram.org/apps
    # ==================================================
    CLIENT_NAME: str = "the_hau5_claim"  # Nombre de la sesión (puede ser cualquiera)
    
    # IMPORTANTE: Reemplaza estos valores con los tuyos propios
    # 1. Ve a https://my.telegram.org/apps
    # 2. Inicia sesión con tu cuenta de Telegram
    # 3. Crea una nueva aplicación o usa una existente
    # 4. Copia el api_id y api_hash y péguelos abajo
    API_ID: int = 25388732  # API ID de Telegram
    API_HASH: str = "f9a7ab46494a09f801e3bde68b93f5c1"  # API HASH de Telegram
    
    # ==================================================

    # ==================================================

    MAX_HOUR_REQUESTS: Union[int, float] = (
        100  # Maximum number of requests per hour (0 - unlimited)
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "bnc-uuid": "c14219da-ab9f-4a66-9358-bef22e74dfdb",
        "device-info": "eyJzY3JlZW5fcmVzb2x1dGlvbiI6Ijg2NCwxNTM2IiwiYXZhaWxhYmxlX3NjcmVlbl9yZXNvbHV0aW9uIjoiODY0LDE1MzYiLCJzeXN0ZW1fdmVyc2lvbiI6IldpbmRvd3MgMTAiLCJicmFuZF9tb2RlbCI6InVua25vd24iLCJzeXN0ZW1fbGFuZyI6ImVzLTQxOSIsInRpbWV6b25lIjoiR01ULTA2OjAwIiwidGltZXpvbmVPZmZzZXQiOjM2MCwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzcuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImxpc3RfcGx1Z2luIjoiUERGIFZpZXdlcixDaHJvbWUgUERGIFZpZXdlcixDaHJvbWl1bSBQREYgVmlld2VyLE1pY3Jvc29mdCBFZGdlIFBERiBWaWV3ZXIsV2ViS2l0IGJ1aWx0LWluIFBERiIsImNhbnZhc19jb2RlIjoiZDFkZDMxYzkiLCJ3ZWJnbF92ZW5kb3IiOiJHb29nbGUgSW5jLiAoSW50ZWwpIiwid2ViZ2xfcmVuZGVyZXIiOiJBTkdMRSAoSW50ZWwsIEludGVsKFIpIFVIRCBHcmFwaGljcyAoMHgwMDAwNDZBMykgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSkiLCJhdWRpbyI6IjEyNC4wNDM0NzUyNzUxNjA3NCIsInBsYXRmb3JtIjoiV2luMzIiLCJ3ZWJfdGltZXpvbmUiOiJBbWVyaWNhL01leGljb19DaXR5IiwiZGV2aWNlX25hbWUiOiJDaHJvbWUgVjEzNy4wLjAuMCAoV2luZG93cykiLCJmaW5nZXJwcmludCI6IjI4MmRkMDQ4NTBiYjczOWVlNjhjYzhmOWExNGQxMjNjIiwiZGV2aWNlX2lkIjoiIiwicmVsYXRlZF9kZXZpY2VfaWRzIjoiIn0=",
        "clienttype": "web",
        "csrftoken": "0f452b5fd6b22552f3c5b968cfe8d89e",
        "fvideo-id": "3348ba6afc04ae228bcfd1431f6c11c76ef27302",
        "fvideo-token": "vwD2b5I/zw2IbuIdCrWzTj6xt+XOfEGWHta2/z/+rG95uVlrin+sCjmzH0XP38vOOXE2FoIXeyFRjlCx43jEGAyKvR/MtZfPGNzP+g/BGtEdTgzAS+2dzi2wVe3Zo5NABQJWgwlSaXc+9tGZBUVh6oUNB2moYtctsu/PyLBMx5nugi+IMENdXeWIWR+bo9EW8=12",
        "x-trace-id": "1218f4e7-d78f-4e98-b85e-894692f82d3b",
        "x-ui-request-trace": "1218f4e7-d78f-4e98-b85e-894692f82d3b",
        "lang": "es-419",
        "Referer": "https://www.binance.com/es/my/wallet/account/payment/cryptobox",
        "Cookie": 'aws-waf-token=31da56a6-d89c-4698-bfbe-60ff8cacda74:EQoAcmCQPGtFAAAA:D/kofpSngWjR9PdEf+JnQz68QXOfL2/J17edBkj0WQA0gNLocTWgCRKs8A2hBFx0tGoUfzgDsrDT+oTpzCWgGRQfHStMSpb/hHrNpGyMY5xIXw5FmamSVuuBVyWrur7l2GL35GlmAgrGSu160tcAIjPovPjKzM3VZmpYx3Qf5nwLguKVxKrIVp6IvjNPa3DhrMQ=; bnc-uuid=c14219da-ab9f-4a66-9358-bef22e74dfdb; _gid=GA1.2.2036873549.1748378167; OptanonAlertBoxClosed=2025-05-27T20:36:09.336Z; lang=es-419; language=es-419; se_gd=RgBEBVh0UDVAgxb0QEBRgZZBxB1FTBRV1ZS9ZVUdllXVADVNWVEF1; se_gsd=AjMmCgpVIDQgCVI2JyY1MAQnCQ1XAAQBVl1GVFxTV1lRJ1NT1; BNC_FV_KEY=3348ba6afc04ae228bcfd1431f6c11c76ef27302; r20t=web.67EA5049C39E77EBF94687084EFDEFAB; r30t=1; cr00=E4C0901BF89294A89A01E5C93DAFFBFA; d1og=web.1096314291.F77A6FFDD334ECDEE6EAA781572ABED4; r2o1=web.1096314291.67182D397C717C23F9C634642210ADA7; f30l=web.1096314291.17D740070DC9EA3A07021279149EF6CC; currentAccount=; logined=y; isAccountsLoggedIn=y; BNC-Location=MX; _gcl_au=1.1.1836210152.1748378289; theme=dark; neo-theme=dark; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221096314291%22%2C%22first_id%22%3A%221971375a82e18ea-0f11d6d7e597a2-26011e51-1327104-1971375a82f2a68%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk3MTM3NWE4MmUxOGVhLTBmMTFkNmQ3ZTU5N2EyLTI2MDExZTUxLTEzMjcxMDQtMTk3MTM3NWE4MmYyYTY4IiwiJGlkZW50aXR5X2xvZ2luX2lkIjoiMTA5NjMxNDI5MSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%221096314291%22%7D%2C%22%24device_id%22%3A%221971375c2c2d94-0058b45bdd71fd0c-26011e51-1327104-1971375c2c32693%22%7D; _uetsid=808734203b3a11f0bab959f24c917555; _uetvid=80874ca03b3a11f0a3c4555bad7c54f3; OptanonConsent=isGpcEnabled=0&datestamp=Wed+May+28+2025+00%3A34%3A42+GMT-0600+(hora+est%C3%A1ndar+central)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d41dde1d-9ef5-48ee-a18b-a73342d09e94&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&intType=1&geolocation=MX%3BCHH&AwaitingReconsent=false; _gat=1; _gat_UA-162512367-1=1; _ga=GA1.1.1895505163.1748378167; _ga_3WP50LGEEC=GS2.1.s1748414083$o3$g0$t1748414084$j59$l0$h0; BNC_FV_KEY_T=101-AfArZ%2BIKGV7S9D50dcmBI%2BEXmL74vgvcILmt0RMX9x5OE9ugySB9KXnWeO8vneBve4MOqHxJwhfZcmLNjGAKyw%3D%3D-W87dj2NvUpcweigyaycm%2BA%3D%3D-c1; BNC_FV_KEY_EXPIRE=1748435684256; p20t=web.1096314291.68DD33B5A5154615688D4A1B6128591E; se_sd=BUDFwVAYFQaBRcRxXVRVgZZA1DxAEETUVFWNYWk5llQUgFVNWVFU1',
        "Origin": "https://www.binance.com",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "Priority": "u=1, i",
        "Sec-Ch-Ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
