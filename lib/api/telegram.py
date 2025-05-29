from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel
import re
import sys # Added for sys.exit

# custom_print is imported before Config to be available for error messages
from source import custom_print
from lib.manipulator import ManipulateToken
# Config import is now handled within __init__ to allow custom_print to be used for errors


class BaseClient:
    def __init__(self):
        try:
            from source.config import Config # Moved import here
            self.config: Config = Config()
        except ImportError:
            custom_print("Error: Configuration file 'source/config.py' not found. Please copy 'source/config.example.py' to 'source/config.py' and fill in your details.", "error")
            sys.exit(1)
        except SyntaxError:
            custom_print("Error: Configuration file 'source/config.py' contains syntax errors. Please correct them.", "error")
            sys.exit(1)
        except Exception as e:
            custom_print(f"Error loading configuration: {e}", "error")
            sys.exit(1)
            
        self.client: TelegramClient = TelegramClient(
            self.config.CLIENT_NAME, self.config.API_ID, self.config.API_HASH
        )
        # Pass config to ManipulateToken constructor
        self.manipulator = ManipulateToken(self.config) 
        self.setup_event_handler()
        self.chat_ids = set()

    async def get_chats(self):
        """Obtiene dinámicamente todos los chats del usuario, excluyendo los que contengan 'intel'"""
        try:
            custom_print("Obteniendo lista de chats...", "info")
            
            # Limpiar la lista de chats monitoreados
            self.chat_ids = set()
            
            # Obtener todos los diálogos
            dialogs = await self.client.get_dialogs()
            
            for dialog in dialogs:
                try:
                    chat = dialog.entity
                    chat_name = ''
                    
                    # Obtener el nombre del chat dependiendo del tipo
                    if hasattr(chat, 'title'):
                        chat_name = getattr(chat, 'title', '').lower()
                    elif hasattr(chat, 'first_name') and hasattr(chat, 'last_name'):
                        chat_name = f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip().lower()
                    elif hasattr(chat, 'first_name'):
                        chat_name = getattr(chat, 'first_name', '').lower()
                    
                    # Verificar si el chat debe ser excluido (que contenga 'intel')
                    exclude_chat = any(exclude.lower() in chat_name for exclude in self.config.EXCLUDE_CHATS_WITH)
                    
                    if not exclude_chat:
                        self.chat_ids.add(chat.id)
                        custom_print(f"Monitoreando chat: {chat_name} (ID: {chat.id})", "info")
                except Exception as e:
                    custom_print(f"Error procesando chat: {str(e)}", "error")
                    continue
            
            custom_print(f"Total de chats monitoreados: {len(self.chat_ids)}", "info")
            
        except Exception as e:
            custom_print(f"Error al obtener chats: {str(e)}", "error")



    def setup_event_handler(self):
        @self.client.on(events.NewMessage())
        async def _(event: events.NewMessage.Event):
            try:
                # Verificar si el mensaje proviene de un chat monitoreado
                if event.chat_id not in self.chat_ids:
                    return
                
                message_text = event.raw_text.strip()
                
                # Buscar mensajes con formato de pregunta/respuesta
                if 'Answer:' in message_text and 'app.binance.com/uni-qr/cart/' in message_text:
                    # Extraer el código del enlace
                    code_match = re.search(r'app\.binance\.com/uni-qr/cart/(\d+)', message_text)
                    if code_match:
                        code = code_match.group(1)
                        # Extraer la respuesta (línea después de 'Answer:')
                        answer_section = message_text.split('Answer:', 1)[1].strip()
                        # Tomar la primera línea no vacía como respuesta
                        answer = next((line.strip() for line in answer_section.split('\n') if line.strip()), '')
                        # Limpiar la respuesta de emojis y espacios extra
                        answer = re.sub(r'[^\w\s-]', '', answer).strip()
                        if answer:
                            await self.process_code_with_answer(code, answer)
                            return
                
                # Búsqueda de códigos alfanuméricos estándar
                try:
                    if not message_text:
                        return
                        
                    # Buscar códigos de 8 caracteres alfanuméricos en mayúsculas
                    # que parezcan códigos de Binance (ejemplo: 3JGF9L8V, QY4ZENDD, EF74690C)
                    tokens = re.findall(r'\b(?!\d+\b)(?![a-z]+\b)[A-Z0-9]{8}\b', message_text)
                    
                    if tokens:
                        # Filtrar tokens que tengan al menos un número y una letra mayúscula
                        # y que no sean solo números
                        valid_tokens = [t for t in tokens if any(c.isdigit() for c in t) 
                                     and any(c.isupper() for c in t) 
                                     and not t.isdigit()]
                        
                        if valid_tokens:
                            custom_print(f"Mensaje de chat {event.chat_id} contiene posibles códigos: {', '.join(valid_tokens)}", "info")
                            
                            # Procesar cada token válido
                            for token in valid_tokens:
                                try:
                                    await self.manipulator.main(token)
                                except Exception as e:
                                    custom_print(f"Error al procesar token {token}: {str(e)}", "error")
                except Exception as e:
                    custom_print(f"Error al procesar mensaje: {str(e)}", "error")
            
            except Exception as e:
                custom_print(f"Error al procesar mensaje: {str(e)}", "error")

    async def process_code_with_answer(self, code: str, answer: str):
        """Procesa un código junto con su respuesta (funcionalidad pendiente)"""
        custom_print(f"Received code '{code}' with answer '{answer}'. This feature is pending implementation.", "warning")

    async def start_client(self):
        """Inicia el cliente y configura los chats"""
        custom_print("Iniciando cliente...", "info")
        await self.client.start(phone=lambda: input('Por favor ingresa tu número de teléfono (con código de país): '))
        
        # Obtener y configurar los chats a monitorear
        await self.get_chats()
        
        if not self.chat_ids:
            custom_print("No se encontraron chats para monitorear. Saliendo...", "error")
            return False
            
        custom_print("Cliente iniciado, monitoreando mensajes...", "info")
        return True

    def start(self):
        """Método principal para iniciar el cliente"""
        custom_print("Iniciando el bot...", "info")
        
        with self.client:
            try:
                self.client.loop.run_until_complete(self.start_client())
                self.client.run_until_disconnected()
            except KeyboardInterrupt:
                custom_print("Bot detenido por el usuario", "info")
            except Exception as e:
                custom_print(f"Error al iniciar el bot: {str(e)}", "error")
