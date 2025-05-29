from dataclasses import dataclass
from typing import Union

@dataclass
class Config:
    # ==================================================
    # CONFIGURACIÓN DE CHATS
    # ==================================================
    # Lista de chats a monitorear (se llenará dinámicamente)
    CHATS = []
    
    # Patrón para excluir chats que contengan estas palabras (case insensitive)
    EXCLUDE_CHATS_WITH = ['intel']

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
    # CONFIGURACIÓN DEL BOT DE TELEGRAM
    # ==================================================
    # Token del bot de Telegram (obtén uno con @BotFather)
    BOT_TOKEN: str = "7826975805:AAETDwAkR0p_J219npFIcf3-N84eu6P0JFI"
    
    # ID del chat de administrador (obtén tu ID de chat con @userinfobot en Telegram)
    ADMIN_CHAT_ID: int = 7392813585  # ID de usuario de Telegram para Alan Gardea
    
    # Número máximo de solicitudes por hora (0 = ilimitado)
    MAX_HOUR_REQUESTS: Union[int, float] = 0  # Desactivado (ilimitado)
    
    # Delay en segundos entre intentos de reclamo
    REQUEST_DELAY_SECONDS: Union[int, float] = 3  # 3 segundos entre solicitudes
    
    # Comandos disponibles
    BOT_COMMANDS = [
        ('start', 'Inicia el bot'),
        ('autoclaim', 'Activa/desactiva el reclamo automático'),
        ('logs', 'Muestra los registros recientes'),
        ('help', 'Muestra la ayuda'),
        ('stop_bot', 'Detiene el bot'),
        ('restart', 'Reinicia el bot')
    ]
    
    # ==================================================
    # CONFIGURACIÓN DE ADMINISTRADOR DEL BOT
    # ==================================================
    # Tu User ID de Telegram. El bot te enviará notificaciones y responderá a tus comandos.
    # Puedes obtener tu User ID hablando con bots como @userinfobot en Telegram.
    # Pon 0 si no quieres activar esta funcionalidad (no recibirás notificaciones ni podrás usar comandos).
    ADMIN_USER_ID: int = 7392813585  # ID de administrador de Alan
    
    # Configuración de encabezados para las solicitudes HTTP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "bnc-level": "0",
        "bnc-location": "MX",
        "bnc-time-zone": "America/Mexico_City",
        "bnc-uuid": "c14219da-ab9f-4a66-9358-bef22e74dfdb",
        "clienttype": "web",
        "content-type": "application/json",
        "cookie": "aws-waf-token=31da56a6-d89c-4698-bfbe-60ff8cacda74:EQoAcmCQPGtFAAAA:D/kofpSngWjR9PdEf+JnQz68QXOfL2/J17edBkj0WQA0gNLocTWgCRKs8A2hBFx0tGoUfzgDsrDT+oTpzCWgGRQfHStMSpb/hHrNpGyMY5xIXw5FmamSVuuBVyWrur7l2GL35GlmAgrGSu160tcAIjPovPjKzM3VZmpYx3Qf5nwLguKVxKrIVp6IvjNPa3DhrMQ=; bnc-uuid=c14219da-ab9f-4a66-9358-bef22e74dfdb; _gid=GA1.2.2036873549.1748378167; OptanonAlertBoxClosed=2025-05-27T20:36:09.336Z; language=es-419; se_gd=RgBEBVh0UDVAgxb0QEBRgZZBxB1FTBRV1ZS9ZVUdllXVADVNWVEF1; se_gsd=AjMmCgpVIDQgCVI2JyY1MAQnCQ1XAAQBVl1GVFxTV1lRJ1NT1; BNC_FV_KEY=3348ba6afc04ae228bcfd1431f6c11c76ef27302; currentAccount=; isAccountsLoggedIn=y; BNC-Location=MX; _gcl_au=1.1.1836210152.1748378289; neo-theme=dark; changeBasisTimeZone=; userPreferredCurrency=USD_USD; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221096314291%22%2C%22first_id%22%3A%221971375a82e18ea-0f11d6d7e597a2-26011e51-1327104-1971375a82f2a68%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_utm_medium%22%3A%22web_share_copy%22%2C%22%24latest_utm_content%22%3A%22pay_universal_link_v2%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk3MTM3NWE4MmUxOGVhLTBmMTFkNmQ3ZTU5N2EyLTI2MDExZTUxLTEzMjcxMDQtMTk3MTM3NWE4MmYyYTY4IiwiJGlkZW50aXR5X2xvZ2luX2lkIjoiMTA5NjMxNDI5MSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%221096314291%22%7D%2C%22%24device_id%22%3A%221971375c2c2d94-0058b45bdd71fd0c-26011e51-1327104-1971375c2c32693%22%7D; theme=dark; futures-layout=pro; language=es; BNC_FV_KEY_T=101-DJtDDzqU8DmODW6hLhngrh8tH3Iiu%2BQI2iIGurhkspxlRGJVqafmOP9aZ%2Fu9vMtx5LgpMsKN%2ByLOy1iLUgrA%2BQ%3D%3D-1Oa3KK8g9F%2FDmcK0ES%2BWJA%3D%3D-65; BNC_FV_KEY_EXPIRE=1748564610830; lang=es-419; se_sd=xIGBBRQQVAQVQ4QkWDQUgZZVgFxYXEQV1QDRYU0NllRVwVlNWVNU1; s9r1=B1C45C1D64D17209BAEB2236948E44BD; r20t=web.6BE9BC80E2A556DC830BE8655A5D8D82; r30t=1; cr00=15BAC9FC0C189D7C2D22435C5F50E367; d1og=web.1096314291.0D89AB6EA6FA908DC69921CDA884324D; r2o1=web.1096314291.2F7110D98900D12D3EBFBDD95AF26008; f30l=web.1096314291.E0C725A0F46183FF60ABEE74063B5D81; logined=y; p20t=web.1096314291.04DE8EB022E1683D0037B459C2261737; _uetsid=808734203b3a11f0bab959f24c917555; _uetvid=80874ca03b3a11f0a3c4555bad7c54f3; OptanonConsent=isGpcEnabled=0&datestamp=Thu+May+29+2025+12%3A32%3A04+GMT-0600+(hora+est%C3%A1ndar+central)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d41dde1d-9ef5-48ee-a18b-a73342d09e94&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&intType=1&geolocation=MX%3BCHH&AwaitingReconsent=false; _ga=GA1.1.1895505163.1748378167; _ga_3WP50LGEEC=GS2.1.s1748543010$o10$g1$t1748543527$j13$l0$h0",
        "csrftoken": "7bb0e7726104895fd52f19cc8a99222b",
        "device-info": "eyJzY3JlZW5fcmVzb2x1dGlvbiI6Ijg2NCwxNTM2IiwiYXZhaWxhYmxlX3NjcmVlbl9yZXNvbHV0aW9uIjoiODY0LDE1MzYiLCJzeXN0ZW1fdmVyc2lvbiI6IldpbmRvd3MgMTAiLCJicmFuZF9tb2RlbCI6InVua25vd24iLCJzeXN0ZW1fbGFuZyI6ImVzLTQxOSIsInRpbWV6b25lIjoiR01ULTA2OjAwIiwidGltZXpvbmVPZmZzZXQiOjM2MCwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzcuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImxpc3RfcGx1Z2luIjoiUERGIFZpZXdlcixDaHJvbWUgUERGIFZpZXdlcixDaHJvbWl1bSBQREYgVmlld2VyLE1pY3Jvc29mdCBFZGdlIFBERiBWaWV3ZXIsV2ViS2l0IGJ1aWx0LWluIFBERiIsImNhbnZhc19jb2RlIjoiZDFkZDMxYzkiLCJ3ZWJnbF92ZW5kb3IiOiJHb29nbGUgSW5jLiAoSW50ZWwpIiwid2ViZ2xfcmVuZGVyZXIiOiJBTkdMRSAoSW50ZWwsIEludGVsKFIpIFVIRCBHcmFwaGljcyAoMHgwMDAwNDZBMykgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSkiLCJhdWRpbyI6IjEyNC4wNDM0NzUyNzUxNjA3NCIsInBsYXRmb3JtIjoiV2luMzIiLCJ3ZWJfdGltZXpvbmUiOiJBbWVyaWNhL01leGljb19DaXR5IiwiZGV2aWNlX25hbWUiOiJDaHJvbWUgVjEzNy4wLjAuMCAoV2luZG93cykiLCJmaW5nZXJwcmludCI6IjI4MmRkMDQ4NTBiYjczOWVlNjhjYzhmOWExNGQxMjNjIiwiZGV2aWNlX2lkIjoiIiwicmVsYXRlZF9kZXZpY2VfaWRzIjoiIn0=",
        "fvideo-id": "3348ba6afc04ae228bcfd1431f6c11c76ef27302",
        "fvideo-token": "u7sBtxDlo6++uSKtZnC+JUUPgXvEYLi2MCg6OU3fXj1/GfBlF5rXxDgLD95p9SWadu/M6knAHzH4kyRY32vLcC0jyWJEyKdqa3fx3efWlfnfvm6+DjgYWUJFd0megZu70RzQrSQZH7E2WDYcaUq982w557W4k9to25mOVuxRSEAp3o2QZ7GKnTAMKTOmHF3T0=6d",
        "lang": "es-419",
        "Origin": "https://www.binance.com",
        "Priority": "u=1, i",
        "Referer": "https://www.binance.com/es/my/wallet/account/payment/cryptobox",
        "Sec-Ch-Ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Passthrough-Token": "",
        "X-Trace-Id": "9b95dad5-8c1f-46ca-94b3-a42489bd789b",
        "X-Ui-Request-Trace": "9b95dad5-8c1f-46ca-94b3-a42489bd789b"
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
