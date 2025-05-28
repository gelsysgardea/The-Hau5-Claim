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
    API_ID: int = 0  # Reemplaza con tu API ID de Telegram
    API_HASH: str = ""  # Reemplaza con tu API HASH de Telegram
    
    # ==================================================
    # CONFIGURACIÓN DEL BOT
    # ==================================================
    # Número máximo de solicitudes por hora (0 = ilimitado)
    MAX_HOUR_REQUESTS: Union[int, float] = 100
    
    # Configuración de encabezados para las solicitudes HTTP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "clienttype": "web",
        "lang": "es-419",
        "Referer": "https://www.binance.com/es/my/wallet/account/payment/cryptobox",
        "Origin": "https://www.binance.com",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "Sec-Ch-Ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
