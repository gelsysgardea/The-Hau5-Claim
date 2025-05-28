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
        timestamp = datetime.now().replace(minute=0, second=0, microsecond=0).timestamp()

        # Reiniciar el contador si ha pasado una hora
        if timestamp > self.last_timestamp:
            self.processed_tokens.clear()
            self.timeout = False
            self.last_timestamp = timestamp
            custom_print("Contador de solicitudes reiniciado para la nueva hora", "info")

        # Verificar si el token ya fue procesado
        if token in self.processed_tokens:
            custom_print(f"Token ya procesado, ignorando: {token}", "info")
            return
            
        # Agregar el token a la lista de procesados ANTES de intentar reclamarlo
        # para evitar intentos duplicados
        self.processed_tokens.append(token)
            
        # Verificar si hemos alcanzado el límite de solicitudes por hora
        if self.config.MAX_HOUR_REQUESTS > 0 and len(self.processed_tokens) >= self.config.MAX_HOUR_REQUESTS:
            custom_print(
                f"Límite de {self.config.MAX_HOUR_REQUESTS} solicitudes por hora alcanzado.",
                "warning"
            )
            self.timeout = True
            return
            
        # Verificar si estamos en modo de espera por captcha o límite de solicitudes
        if self.timeout:
            custom_print("En modo de espera debido a un error previo", "warning")
            return

        # Verificar si el token parece un código válido (contiene números y letras)
        if not any(c.isdigit() for c in token) or not any(c.isalpha() for c in token):
            custom_print(f"Ignorando token que no parece un código válido: {token}", "warning")
            return
            
        custom_print(f"Procesando código: {token}", "info")
        
        try:
            # Espera fija de 3 segundos entre solicitudes
            await asyncio.sleep(3)
            result = await self.api.send_request(token)
            
            # Si la respuesta es None, manejarlo como un error
            if result is None:
                custom_print(f"❌ Error: Respuesta vacía de la API para el código {token}", "error")
                return
                
            # Si la respuesta es una cadena, verificar si es un error
            if isinstance(result, str) and result not in ["captcha", "too_many_requests", "processed"]:
                custom_print(f"❌ Error: Respuesta inesperada ({result}) para el código {token}", "error")
                return
                
            # Procesar el resultado
            match result:
                case "captcha":
                    custom_print("¡Captcha detectado! Se requiere intervención manual.", "error")
                    self.timeout = True
                    
                case "too_many_requests":
                    custom_print("Demasiadas solicitudes. Esperando...", "warning")
                    self.timeout = True
                    
                case "claimed":
                    custom_print(f"✅ Código {token} reclamado exitosamente!", "success")
                    
                case "processed":
                    custom_print(f"🔍 Código {token} ya fue procesado.", "info")
                    
                case "error":
                    custom_print(f"❌ Error al procesar el código {token}", "error")
                    
                case _:
                    custom_print(f"⚠️ Respuesta inesperada del servidor: {result}", "warning")
                    
        except Exception as e:
            custom_print(f"❌ Error al procesar el token {token}: {str(e)}", "error")
