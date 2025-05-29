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


class ManipulateToken:
    def __init__(self, config: 'Config'): # Added config parameter with string literal type hint
        self.config: 'Config' = config # Set config from parameter, type hint as string literal
        # Pass config to BinanceAPI constructor
        self.api: BinanceAPI = BinanceAPI(self.config)

        self.last_timestamp = 0
        self.processed_tokens: List[str] = [] # Hourly cache
        self.timeout: bool = False
        self.last_processed: bool = True
        
        self.claimed_codes_file: str = "data/claimed_codes.json"
        self.permanently_claimed_codes: Set[str] = set()
        self._ensure_data_directory()
        self._load_claimed_codes()

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

    async def main(self, token: str) -> None:
        # Primero, verificar si el token ya está en la lista de reclamados permanentemente
        if token in self.permanently_claimed_codes:
            custom_print(f"Token {token} ya fue reclamado y guardado permanentemente. Ignorando.", "info")
            return

        timestamp = datetime.now().replace(minute=0, second=0, microsecond=0).timestamp()

        # Reiniciar el contador si ha pasado una hora
        if timestamp > self.last_timestamp:
            self.processed_tokens.clear()
            self.timeout = False
            self.last_timestamp = timestamp
            custom_print("Contador de solicitudes reiniciado para la nueva hora", "info")

        # Verificar si el token ya fue procesado en esta hora (cache horario)
        if token in self.processed_tokens:
            custom_print(f"Token {token} ya procesado en esta hora. Ignorando.", "info")
            return
            
        # Agregar el token a la lista de procesados de esta hora ANTES de intentar reclamarlo
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
            # Use configurable delay with a safe default
            delay = getattr(self.config, 'REQUEST_DELAY_SECONDS', 3)
            await asyncio.sleep(delay)
            result = await self.api.send_request(token)
            
            # Procesar el resultado
            match result:
                case "claimed":
                    custom_print(f"✅ Código {token} reclamado exitosamente!", "success")
                    self.permanently_claimed_codes.add(token) # Add to in-memory set
                    self._save_claimed_code(token) # Save to persistent storage
                case "processed":
                    custom_print(f"🔍 Código {token} ya fue procesado o es inválido.", "info")
                case "captcha":
                    custom_print("¡Captcha detectado! Se requiere intervención manual. Pausando procesamiento.", "error")
                    self.timeout = True
                case "too_many_requests":
                    custom_print("Límite de solicitudes alcanzado (too_many_requests). Pausando procesamiento.", "warning")
                    self.timeout = True
                case "session_expired":
                    custom_print(f"❌ Sesión de Binance expirada al intentar procesar {token}. Actualiza credenciales/cookies y reinicia. Pausando.", "error")
                    self.timeout = True
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
                case _:
                    custom_print(f"⚠️ Respuesta inesperada del servidor: '{result}' para el código {token}. Considerar como error y pausar.", "warning")
                    self.timeout = True # Default to pausing on unknown states
                    
        except Exception as e:
            custom_print(f"❌ Excepción crítica al procesar el token {token}: {str(e)}", "error")
            self.timeout = True # Pause on any unhandled exception during processing
