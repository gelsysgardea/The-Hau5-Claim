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
        # Pass config and self (BaseClient instance) to ManipulateToken constructor
        self.manipulator = ManipulateToken(self.config, self) 
        
        self.is_monitoring_active: bool = False # Initialize monitoring status
        
        self.setup_event_handler() # For general messages
        self.setup_command_handler() # For admin commands
        
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
                # Do not process if monitoring is inactive or chat is not in the list
                if not self.is_monitoring_active:
                    return
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

    async def send_admin_notification(self, message: str):
        """Sends a notification message to the admin user."""
        admin_id = getattr(self.config, 'ADMIN_USER_ID', 0)
        if not admin_id or admin_id == 0:
            custom_print(f"Notificación para admin no enviada (ADMIN_USER_ID no configurado): {message}", "warning")
            return

        try:
            await self.client.send_message(admin_id, message, parse_mode='md')
            custom_print(f"Notificación enviada al admin ({admin_id}): {message}", "info")
        except Exception as e:
            custom_print(f"Error al enviar notificación al admin ({admin_id}): {str(e)}", "error")

    def setup_command_handler(self):
        """Sets up the event handler for admin commands."""
        admin_id = getattr(self.config, 'ADMIN_USER_ID', 0)
        if not admin_id or admin_id == 0:
            custom_print("ADMIN_USER_ID no está configurado o es 0. Los comandos de administrador estarán deshabilitados.", "warning")
            return

        @self.client.on(events.NewMessage(from_users=admin_id))
        async def admin_command_handler(event: events.NewMessage.Event):
            command_text = event.raw_text.strip().lower()
            sender_id = event.sender_id
            
            custom_print(f"Comando recibido de ADMIN ({sender_id}): '{command_text}'", "info")

            if command_text == "/start_bot":
                if self.is_monitoring_active:
                    await event.respond("🤖 El monitoreo ya está activo.")
                    custom_print("Comando /start_bot ignorado: monitoreo ya activo.", "info")
                else:
                    self.is_monitoring_active = True
                    await self.get_chats() # Refresh chat list on start
                    await event.respond("🤖 Monitoreo iniciado. Escuchando nuevos códigos...")
                    custom_print("Monitoreo iniciado por comando de administrador.", "success")
            elif command_text == "/stop_bot":
                if not self.is_monitoring_active:
                    await event.respond("🛑 El monitoreo ya está detenido.")
                    custom_print("Comando /stop_bot ignorado: monitoreo ya detenido.", "info")
                else:
                    self.is_monitoring_active = False
                    await event.respond("🛑 Monitoreo detenido.")
                    custom_print("Monitoreo detenido por comando de administrador.", "warning")
            elif command_text == "/status_bot":
                status_message = f"🤖 Estado del monitoreo: {'Activo ✅' if self.is_monitoring_active else 'Detenido ❌'}"
                if self.is_monitoring_active:
                    status_message += f"\n👁️ Monitoreando {len(self.chat_ids)} chat(s)."
                await event.respond(status_message)
                custom_print(f"Comando /status_bot ejecutado. Estado: {'Activo' if self.is_monitoring_active else 'Detenido'}", "info")
            # else:
                # Optional: Respond to unknown commands or ignore them
                # await event.respond("❓ Comando desconocido.")

    async def process_code_with_answer(self, code: str, answer: str):
        """Procesa un código junto con su respuesta (funcionalidad pendiente)"""
        custom_print(f"Received code '{code}' with answer '{answer}'. This feature is pending implementation.", "warning")

    async def start_client(self):
        """Inicia el cliente de Telegram y notifica al administrador."""
        custom_print("Iniciando cliente...", "info")
        try:
            # Prompt for phone and code if not already authorized
            await self.client.start(
                phone=lambda: input('Por favor ingresa tu número de teléfono (con código de país): ')
            )
            custom_print("Cliente de Telegram conectado exitosamente.", "info")

            # Notify admin that bot is online and waiting for /start_bot
            await self.send_admin_notification(
                "🤖 Bot en línea. Esperando comando `/start_bot` para iniciar el monitoreo de chats."
            )
            
            # No longer calling get_chats() here or checking self.chat_ids
            # self.is_monitoring_active is False by default.
            
            custom_print("Cliente iniciado, esperando comandos del administrador...", "info")
            return True # Indicates successful client connection

        except Exception as e:
            custom_print(f"Error severo durante el inicio del cliente de Telegram: {str(e)}", "error")
            # Consider re-raising or handling more specifically if needed
            return False # Indicates failure to connect client

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
