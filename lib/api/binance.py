import re
import json
import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING # Added TYPE_CHECKING

import aiohttp

# from source import Config -> Removed
from source import custom_print

if TYPE_CHECKING:
    from source.config import Config # For type hinting


class BinanceAPI:
    def __init__(self, config: 'Config'): # Added config parameter with string literal type hint
        self.config: 'Config' = config # Set config from parameter, type hint as string literal
        self.response: Optional[aiohttp.ClientResponse] = None

    async def send_request(self, redpacket: str) -> str:
        """
        Envía una solicitud a la API de Binance para reclamar un código de criptocaja.
        
        Args:
            redpacket (str): Código de la criptocaja a reclamar.
            
        Returns:
            str: Estado del reclamo ("claimed", "captcha", "too_many_requests", "processed")
        """
        if not redpacket or not isinstance(redpacket, str) or len(redpacket) < 5:
            custom_print("Código de criptocaja inválido", "error")
            return "processed"

        url = "https://www.binance.com/bapi/pay/v1/private/binance-pay/gift-box/code/grabV2"
        payload = {
            "channel": "DEFAULT",
            "grabCode": redpacket.strip(),
            "scene": None
        }

        try:
            # Intentar conectar con la API de Binance
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.config.headers,
                    json=payload,
                    timeout=30
                ) as response:
                    self.response = response
                    
                    # Verificar si la respuesta es exitosa
                    if response.status != 200:
                        error_msg = f"Error en la respuesta HTTP: {response.status}"
                        custom_print(error_msg, "error")
                        return f"http_error_{response.status}"
                    
                    try:
                        response_json = await response.json()
                    except json.JSONDecodeError:
                        custom_print("Error al decodificar la respuesta JSON. No se pudo procesar el contenido.", "error")
                        return "json_decode_error"
                    
                    # Procesar la respuesta
                    return await self._process_response(response_json, redpacket)
                    
        except asyncio.TimeoutError:
            custom_print("Tiempo de espera agotado al conectar con Binance.", "error")
            return "timeout_error"
            
        except aiohttp.ClientError as e:
            custom_print(f"Error de conexión de red: {str(e)}", "error")
            return "network_error"
            
        except Exception as e:
            custom_print(f"Error inesperado durante el envío de la solicitud: {str(e)}", "error")
            return "unknown_error_send_request"
    
    async def _process_response(self, response: Dict[str, Any], redpacket: str) -> str:
        """Procesa la respuesta de la API de Binance."""
        try:
            # Verificar si la respuesta es None o no es un diccionario
            if not response or not isinstance(response, dict):
                custom_print("Error: Formato de respuesta de la API no válido o respuesta vacía.", "error")
                return "invalid_api_response_format"
            
            # Respuesta exitosa
            if isinstance(response.get("success", False), bool) and response.get("success"):
                # Extraer datos de manera segura
                data = response.get("data", {})
                currency = data.get("currency", "N/A")
                amount = data.get("grabAmountStr", "0")
                custom_print(f"¡Caja reclamada exitosamente! {amount} {currency}", "success")
                return {"status": "claimed", "data": {"amount": amount, "currency": currency}}
            
            # Manejo de errores conocidos
            error_code = response.get("code", "")
            error_message = response.get("message", "Error desconocido")
            
            # Captcha detectado
            if "validateId" in response.get("data", {}):
                custom_print("Se ha detectado un CAPTCHA. Por favor, resuélvelo manualmente.", "error")
                return "captcha"
            
            # Límite de solicitudes excedido
            if error_code == "403067":
                # Intentar extraer el tiempo de espera del mensaje de error
                wait_time = "1 hora"  # Valor por defecto
                match = re.search(r"(\d+):(\d+)", error_message)
                if match:
                    hours, minutes = match.groups()
                    wait_time = f"{hours} horas y {minutes} minutos"
                custom_print(f"Demasiadas solicitudes. Espera {wait_time} antes de intentar de nuevo.", "warning")
                return "too_many_requests"
            
            # Caja ya reclamada
            if error_code == "403802":
                custom_print(f"La criptocaja {redpacket} ya ha sido reclamada.", "info")
                return "processed"
            
            # Código inválido
            if error_code in ["403803", "PAY4001COM000"]:
                custom_print(f"Código de criptocaja inválido: {redpacket}", "error")
                return "processed"
            
            # Sesión expirada
            if error_code == "100002001":
                custom_print("La sesión ha expirado. Por favor, inicia sesión nuevamente.", "error")
                return "session_expired"
            
            # Otro tipo de error
            error_key = f"binance_api_error_{error_code}" if error_code else "binance_api_error_unknown"
            custom_print(f"Error en la respuesta de Binance: {error_message} (Código: {error_code if error_code else 'Desconocido'})", "error")
            return error_key
            
        except Exception as e:
            custom_print(f"Error inesperado al procesar la respuesta de Binance: {str(e)}", "error")
            return "unknown_error_process_response"
