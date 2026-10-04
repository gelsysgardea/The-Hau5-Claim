import os
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
    API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0") or 0)
    API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    
    # ==================================================
    # CONFIGURACIÓN DEL BOT DE TELEGRAM
    # ==================================================
    # Token del bot de Telegram (obtén uno con @BotFather)
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # ID del chat de administrador (obtén tu ID de chat con @userinfobot en Telegram)
    ADMIN_CHAT_ID: int = int(os.getenv("TELEGRAM_ADMIN_ID", "0") or 0)
    
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
    ADMIN_USER_ID: int = int(os.getenv("TELEGRAM_ADMIN_ID", "0") or 0)
    
    # Configuración de encabezados para las solicitudes HTTP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "bnc-level": "0",
        "bnc-location": "MX",
        "bnc-time-zone": "America/Mexico_City",
        "bnc-uuid": os.getenv("BNC_UUID", ""),
        "clienttype": "web",
        "content-type": "application/json",
        "cookie": os.getenv("BINANCE_COOKIE", ""),
        "csrftoken": os.getenv("CSRF_TOKEN", ""),
        "device-info": os.getenv("DEVICE_INFO", ""),
        "fvideo-id": os.getenv("FVIDEO_ID", ""),
        "fvideo-token": os.getenv("FVIDEO_TOKEN", ""),
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
        "X-Trace-Id": os.getenv("X_TRACE_ID", ""),
        "X-Ui-Request-Trace": os.getenv("X_UI_REQUEST_TRACE", "")
    }

    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
