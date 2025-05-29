from datetime import datetime
from typing import List, Set

import asyncio
import random
import json
import os
from typing import List, Set, TYPE_CHECKING # Added TYPE_CHECKING

from lib import BinanceAPI
# from source.config import Config -> Removed
from source.utils import custom_print

if TYPE_CHECKING:
    from source.config import Config # For type hinting
    from lib.api.telegram import BaseClient # Added for type hinting


class ManipulateToken:
    def __init__(self, config: 'Config', client_handler: 'BaseClient'): # Added client_handler
        self.config: 'Config' = config 
        self.client_handler: 'BaseClient' = client_handler # Store client_handler
        # Pass config to BinanceAPI constructor
        self.api: BinanceAPI = BinanceAPI(self.config)

        self.last_timestamp = 0
        self.processed_tokens: List[str] = [] # Cache de sesión
        self.successful_claims: Dict[str, dict] = {}  # Diccionario para códigos canjeados con éxito
        self.timeout: bool = False
        self.last_processed: bool = True
        
        self.claimed_codes_file: str = "data/claimed_codes.json"
        self.successful_claims_file: str = "data/successful_claims.json"
        self.permanently_claimed_codes: Set[str] = set()
        self._ensure_data_directory()
        self._load_claimed_codes()
        self._load_successful_claims()

    def _ensure_data_directory(self):
        """Ensures the data directory exists."""
        os.makedirs(os.path.dirname(self.claimed_codes_file), exist_ok=True)

    def _load_claimed_codes(self):
        """Loads permanently claimed codes from the JSON file."""
        try:
            if os.path.exists(self.claimed_codes_file):
                with open(self.claimed_codes_file, 'r') as f:
                    codes_list = json.load(f)
                    if isinstance(codes_list, list):
                        self.permanently_claimed_codes = set(codes_list)
                        custom_print(f"Cargados {len(self.permanently_claimed_codes)} códigos reclamados permanentemente.", "info")
                    else:
                        custom_print(f"Error: El archivo de códigos reclamados ({self.claimed_codes_file}) no contiene una lista válida. Iniciando con un conjunto vacío.", "error")
                        self.permanently_claimed_codes = set()
            else:
                custom_print(f"Archivo de códigos reclamados ({self.claimed_codes_file}) no encontrado. Se creará uno nuevo al reclamar el primer código.", "info")
        except json.JSONDecodeError:
            custom_print(f"Error al decodificar JSON del archivo de códigos reclamados ({self.claimed_codes_file}). Verifique el archivo o elimínelo para empezar de nuevo. Iniciando con un conjunto vacío.", "error")
            self.permanently_claimed_codes = set()
        except Exception as e:
            custom_print(f"Error inesperado al cargar códigos reclamados: {str(e)}", "error")
            self.permanently_claimed_codes = set()

    def _save_claimed_code(self, token: str):
        """Saves a newly claimed token to the JSON file and updates the in-memory set."""
        if token in self.permanently_claimed_codes: # Should already be added to set before calling
            pass # Already in set, file will be updated with current set
        
        self.permanently_claimed_codes.add(token) # Ensure it's in the set

        self._ensure_data_directory() # Ensure directory exists before writing
        try:
            # Read current codes, update, then write to avoid losing data if file was modified externally (unlikely here)
            # For simplicity and given this is single-threaded access, we can just write the whole current set.
            # If concurrent access was a concern, a read-modify-write with file locking would be needed.
            current_codes_list = list(self.permanently_claimed_codes) # Convert set to list for JSON
            with open(self.claimed_codes_file, 'w') as f:
                json.dump(current_codes_list, f, indent=4)
            custom_print(f"Código {token} guardado permanentemente en {self.claimed_codes_file}.", "info")
        except IOError as e:
            custom_print(f"Error de E/S al guardar el código {token} en {self.claimed_codes_file}: {str(e)}", "error")
        except Exception as e:
            custom_print(f"Error inesperado al guardar código reclamado {token}: {str(e)}", "error")
            
    def _load_successful_claims(self):
        """Carga los códigos canjeados con éxito desde el archivo."""
        try:
            if os.path.exists(self.successful_claims_file):
                with open(self.successful_claims_file, 'r') as f:
                    self.successful_claims = json.load(f)
                    custom_print(f"Cargados {len(self.successful_claims)} códigos canjeados con éxito.", "info")
            else:
                self.successful_claims = {}
                custom_print("No se encontró archivo de códigos canjeados. Se creará uno nuevo.", "info")
        except Exception as e:
            self.successful_claims = {}
            custom_print(f"Error al cargar códigos canjeados: {str(e)}", "error")
            
    def _save_successful_claims(self):
        """Guarda los códigos canjeados con éxito en el archivo."""
        try:
            with open(self.successful_claims_file, 'w') as f:
                json.dump(self.successful_claims, f, indent=4)
        except Exception as e:
            custom_print(f"Error al guardar códigos canjeados: {str(e)}", "error")
            
    async def get_claim_summary(self) -> str:
        """Genera un resumen de los códigos canjeados con éxito."""
        if not self.successful_claims:
            return "No se han canjeado códigos con éxito aún."
            
        total_codes = len(self.successful_claims)
        total_value = sum(float(data['amount']) for data in self.successful_claims.values() if 'amount' in data)
        
        summary = [
            "📊 *RESUMEN DE CÓDIGOS CANJEADOS*",
            f"• Total de códigos: {total_codes}",
            f"• Valor total: ${total_value:.2f} USD",
            "",
            "*Últimos 5 códigos exitosos:*"
        ]
        
        # Obtener los últimos 5 códigos exitosos
        last_codes = list(self.successful_claims.items())[-5:]
        for code, data in last_codes:
            amount = data.get('amount', '0')
            date = data.get('date', 'Fecha desconocida')
            summary.append(f"- {code}: ${amount} USD ({date})")
            
        return "\n".join(summary)

    async def main(self, token: str) -> None:
        # Primero, verificar si el token ya está en la lista de reclamados permanentemente
        if token in self.permanently_claimed_codes:
            custom_print(f"Token {token} ya fue procesado anteriormente. Ignorando.", "info")
            return

        # Verificar si el token ya fue procesado en esta ejecución (caché de sesión)
        if token in self.processed_tokens:
            custom_print(f"Token {token} ya fue procesado en esta sesión. Ignorando.", "info")
            return
            
        # Agregar el token a la lista de procesados de esta sesión
        self.processed_tokens.append(token)
        
        # Registrar el código como procesado permanentemente
        self.permanently_claimed_codes.add(token)
        self._save_claimed_code(token)
        custom_print(f"Código {token} registrado. Intentando canjear...", "info")
            
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

        # Verificar si el token es un código alfanumérico válido (solo letras mayúsculas y números)
        if not token.isalnum() or not token.isupper() or len(token) != 8:
            custom_print(f"Ignorando token que no cumple con el formato de código válido (8 caracteres alfanuméricos en mayúsculas): {token}", "warning")
            return
            
        # Verificar que el token contenga al menos un número y una letra
        if not any(c.isdigit() for c in token) or not any(c.isalpha() for c in token):
            custom_print(f"Ignorando token que no contiene tanto números como letras: {token}", "warning")
            return
            
        custom_print(f"Procesando código: {token}", "info")
        
        try:
            # Use configurable delay with a safe default
            delay = getattr(self.config, 'REQUEST_DELAY_SECONDS', 3)
            await asyncio.sleep(delay)
            result = await self.api.send_request(token)
            
            response_status = ""
            claimed_data = None

            if isinstance(result, dict) and result.get("status") == "claimed":
                response_status = "claimed"
                claimed_data = result.get("data")
            elif isinstance(result, str):
                response_status = result
            else:
                custom_print(f"Respuesta inesperada de API: {result}", "error")
                response_status = "unknown_api_response"

            # Procesar el resultado
            match response_status:
                case "claimed":
                    amount = claimed_data.get("amount", "N/A") if claimed_data else "N/A"
                case "processed":
                    custom_print(f"🔍 Código {token} ya fue procesado o es inválido.", "info")
                case "captcha":
                    custom_print("¡Captcha detectado! Se requiere intervención manual. Pausando procesamiento.", "error")
                    self.timeout = True
                    await self.client_handler.send_admin_notification(f"🚫 ¡Captcha detectado en Binance para el código `{token}`! Se requiere intervención manual. El bot se ha detenido temporalmente.")
                case "too_many_requests":
                    custom_print("Límite de solicitudes alcanzado (too_many_requests). Pausando procesamiento.", "warning")
                    self.timeout = True
                    await self.client_handler.send_admin_notification(f"⏳ Demasiadas solicitudes a Binance procesando el código `{token}`. El bot esperará un tiempo.")
                case "session_expired":
                    custom_print(f"❌ Sesión de Binance expirada al intentar procesar {token}. Actualiza credenciales/cookies y reinicia. Pausando.", "error")
                    self.timeout = True
                    await self.client_handler.send_admin_notification(f"⚠️ ¡Sesión de Binance expirada! El bot necesita reconfiguración/reinicio de sesión para el código `{token}`.")
                case "timeout_error":
                    custom_print(f"❌ Timeout de red al intentar reclamar {token}. Reintentando con el próximo token si es posible.", "error")
                case "network_error":
                    custom_print(f"❌ Error de red (aiohttp.ClientError) al intentar reclamar {token}. Reintentando con el próximo token si es posible.", "error")
                case status if "http_error_" in status:
                    http_status_code = status.split('_')[-1]
                    custom_print(f"❌ Error HTTP {http_status_code} de Binance al intentar reclamar {token}. Pausando procesamiento.", "error")
                    # Consider setting self.timeout = True if certain HTTP errors are persistent
                    # For now, only printing, but 4xx errors might warrant a pause.
                    # Example: if http_status_code.startswith("4"): self.timeout = True
                case "json_decode_error":
                    custom_print(f"❌ Error decodificando respuesta JSON de Binance para {token}. Podría ser un problema temporal o de API. Pausando.", "error")
                    self.timeout = True
                case "unknown_error_send_request":
                    custom_print(f"❌ Error desconocido (envío) al procesar {token}. Pausando.", "error")
                    self.timeout = True
                case "invalid_api_response_format":
                    custom_print(f"❌ Formato de respuesta inválido de API Binance para {token}. Pausando.", "error")
                    self.timeout = True
                case "unknown_error_process_response":
                    custom_print(f"❌ Error desconocido (procesamiento respuesta) para {token}. Pausando.", "error")
                    self.timeout = True
                case status if "binance_api_error_" in status:
                    api_error_code = status.split('binance_api_error_')[-1]
                    custom_print(f"❌ Error específico de API Binance '{api_error_code}' para {token}. Pausando.", "error")
                    self.timeout = True # Most API errors suggest a pause
                    # Consider adding admin notification for persistent API errors if needed
                case "unknown_api_response": # Handling the explicitly set unknown type
                    custom_print(f"⚠️ Respuesta desconocida de la API procesando {token}. Pausando.", "warning")
                    self.timeout = True
                case _: # Default catch-all for other string responses or unexpected response_status
                    custom_print(f"⚠️ Respuesta/Estado inesperado del servidor: '{response_status}' para el código {token}. Considerar como error y pausar.", "warning")
                    self.timeout = True # Default to pausing on unknown states
                    
        except Exception as e:
            custom_print(f"❌ Excepción crítica al procesar el token {token}: {str(e)}", "error")
            self.timeout = True # Pause on any unhandled exception during processing
