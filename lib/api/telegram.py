from datetime import datetime
import re
import sys
import asyncio
from typing import Optional, Dict, List, Union

from telethon import TelegramClient, events, Button
from telethon.tl.types import User, Chat, Channel
from telethon.sync import TelegramClient as SyncTelegramClient

# custom_print is imported before Config to be available for error messages
from source import custom_print
from lib.manipulator import ManipulateToken
# Config import is now handled within __init__ to allow custom_print to be used for errors

class BaseClient:
    def __init__(self):
        try:
            from source.config import Config
            self.config: Config = Config()
            
            # Mostrar configuración cargada (sin datos sensibles)
            print("🔧 Configuración cargada:")
            print(f"- API_ID: {'*' * 8}{str(self.config.API_ID)[-2:] if self.config.API_ID else 'No configurado'}")
            print(f"- ADMIN_CHAT_ID: {self.config.ADMIN_CHAT_ID}")
            print(f"- BOT_TOKEN: {'*' * 10}{self.config.BOT_TOKEN[-5:] if self.config.BOT_TOKEN else 'No configurado'}")
            print("-" * 50)
            
            # Patrones para detectar códigos en diferentes formatos
            self.code_patterns = [
                r'\b[A-Z0-9]{8,10}\b',  # Códigos de 8-10 caracteres alfanuméricos
                r'(?i)code:?\s*([A-Z0-9]{8,10})',  # Formato "Code: ABC12345"
                r'🔑\s*Code:?\s*([A-Z0-9]{8,10})',  # Formato con emoji de llave
                r'redpack(et)?\s*code:?\s*([A-Z0-9]{8,10})',  # Formato "Redpack code: ABC12345"
                r'\n([A-Z0-9]{8,10})\n',  # Código en una línea por sí solo
                r'([A-Z0-9]{4}[ -]?[A-Z0-9]{4})'  # Códigos con guión o espacio en medio
            ]
            
        except ImportError:
            custom_print("Error: Configuration file 'source/config.py' not found. Please copy 'source/config.example.py' to 'source/config.py' and fill in your details.", "error")
            sys.exit(1)
        except SyntaxError as e:
            custom_print(f"Error: Configuration file 'source/config.py' contains syntax errors: {e}", "error")
            sys.exit(1)
        except Exception as e:
            custom_print(f"Error loading configuration: {e}", "error")
            sys.exit(1)
            
    def extract_codes(self, text):
        """Extrae códigos de un texto usando múltiples patrones"""
        codes = set()
        
        # Limpiar el texto de caracteres especiales que podrían interferir
        clean_text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', ' ', text)
        
        # Probar cada patrón
        for pattern in self.code_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Si el patrón tiene grupos, tomar el primer grupo que coincida
                code = match[0] if isinstance(match, tuple) else match
                # Limpiar y estandarizar el código
                code = re.sub(r'[^A-Z0-9]', '', code.upper())
                if 8 <= len(code) <= 10:  # Solo códigos de 8 a 10 caracteres
                    codes.add(code)
        
        return list(codes)
        
    def log(self, message, level="info"):
        """Función de registro unificada"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}")
        
    def initialize_client(self):
        """Inicializa el cliente de Telegram"""
        try:
            # Inicializar el cliente de Telegram con el bot token
            self.client = TelegramClient(
                'bot_session',
                self.config.API_ID,
                self.config.API_HASH
            ).start(bot_token=self.config.BOT_TOKEN)
            
            # Configurar el manejador de comandos
            self.setup_command_handlers()
            
            # Inicializar el manipulador de tokens
            self.manipulator = ManipulateToken(self.config, self)  # Pass self as client_handler
            # Cargar códigos canjeados existentes
            self.manipulator._load_successful_claims()       
            # Estado del bot - Activar monitoreo por defecto
            self.is_monitoring_active = True
            self.auto_claim_active = True
            self.chat_ids = set()
            
            # Agregar el chat del administrador a la lista de monitoreo
            if self.config.ADMIN_CHAT_ID:
                self.chat_ids.add(self.config.ADMIN_CHAT_ID)
            
            # Configurar comandos del bot
            self.setup_bot_commands()
            
            self.log("Bot inicializado correctamente", "info")
            return True
            
        except Exception as e:
            self.log(f"Error al inicializar el cliente de Telegram: {str(e)}", "error")
            return False

    async def get_chats(self):
        """Maneja la configuración de los chats a monitorear para bots"""
        try:
            custom_print("Configurando chats para monitoreo...\n", "info")
            
            # Limpiar la lista de chats monitoreados
            self.chat_ids = set()
            
            # Obtener el ID del chat actual (donde se ejecutó el comando)
            chat_id = self.config.ADMIN_CHAT_ID  # Asumimos que está configurado en config.py
            
            if not chat_id:
                custom_print("Error: No se ha configurado un chat de administrador. Por favor, configura ADMIN_CHAT_ID en config.py", "error")
                return
            
            # Agregar el chat actual a la lista de monitoreo
            self.chat_ids.add(chat_id)
            
            # Obtener información del chat
            try:
                chat = await self.client.get_entity(chat_id)
                chat_title = getattr(chat, 'title', 'Chat privado')
                custom_print(f"\n=== CHAT SELECCIONADO ===", "success")
                custom_print(f"- {chat_title} (ID: {chat_id})", "success")
                custom_print("\nEl bot ahora está monitoreando este chat.", "success")
                
                # Enviar mensaje de confirmación
                await self.client.send_message(
                    chat_id,
                    "✅ Bot configurado correctamente. Ahora estoy monitoreando este chat para códigos de criptocajas."
                    "\n\nEnvía /help para ver los comandos disponibles."
                )
                
            except Exception as e:
                custom_print(f"Error al obtener información del chat: {str(e)}", "error")
            
        except Exception as e:
            custom_print(f"Error al configurar los chats: {str(e)}", "error")



    def setup_event_handler(self):
        @self.client.on(events.NewMessage())
        async def _(event: events.NewMessage.Event):
            try:
                # Registro detallado del mensaje recibido
                custom_print(f"\n📨 Mensaje recibido - ID: {event.id}", "debug")
                custom_print(f"📝 Contenido: {event.raw_text}", "debug")
                custom_print(f"👤 Remitente ID: {event.sender_id}", "debug")
                custom_print(f"💬 Chat ID: {event.chat_id} (Privado: {event.is_private})", "debug")
                
                # Ignorar mensajes propios
                if hasattr(event.sender, 'is_self') and event.sender.is_self:
                    custom_print("Ignorando mensaje propio", "debug")
                    return
                
                # Verificar si el mensaje es relevante
                is_relevant = False
                
                # Verificar si es un mensaje del administrador
                is_admin_chat = (event.is_private and event.sender_id == self.config.ADMIN_CHAT_ID)
                
                # Verificar si es un mensaje de un chat monitoreado
                is_monitored_chat = event.chat_id in self.chat_ids
                
                # Verificar si es un mensaje en un grupo/canal donde estamos mencionados
                is_mentioned = False
                if hasattr(event, 'message') and hasattr(event.message, 'mentioned'):
                    is_mentioned = event.message.mentioned
                
                custom_print(f"Admin: {is_admin_chat}, Chat monitoreado: {is_monitored_chat}, Mencionado: {is_mentioned}", "debug")
                
                # Procesar mensajes del admin, de chats monitoreados o donde nos mencionen
                if not (is_admin_chat or is_monitored_chat or is_mentioned):
                    custom_print("Mensaje no relevante, ignorando...", "debug")
                    return
                    
                # Si llegamos aquí, el mensaje es relevante
                custom_print("✅ Mensaje relevante detectado, procesando...", "debug")
                    
                custom_print("✅ Mensaje aceptado para procesamiento", "debug")
                
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
                
                # Búsqueda de códigos en el mensaje
                try:
                    if not message_text:
                        custom_print("Mensaje vacío, ignorando...", "debug")
                        return
                        
                    # Si es un comando, lo manejamos aparte
                    if message_text.startswith('/'):
                        custom_print(f"Comando detectado: {message_text}", "debug")
                        return
                    
                    # Extraer códigos del mensaje
                    codes = self.extract_codes(message_text)
                    if not codes:
                        custom_print("No se encontraron códigos en el mensaje", "debug")
                        return
                        
                    custom_print(f"🔍 Códigos detectados en el mensaje: {', '.join(codes)}", "info")
                    
                    # Procesar cada código encontrado
                    for code in codes:
                        try:
                            custom_print(f"Procesando código: {code}", "info")
                            await self.manipulator.main(code)
                            # Pequeña pausa entre códigos
                            await asyncio.sleep(1)
                        except Exception as e:
                            custom_print(f"Error al procesar código {code}: {str(e)}", "error")
                    return
                    
                    # Mostrar información de depuración
                    self.log(f"🔍 Analizando mensaje:")
                    self.log(f"{message_text}")
                    
                    # Extraer códigos usando la función mejorada
                    valid_tokens = self.extract_codes(message_text)
                    self.log(f"📋 Códigos detectados: {valid_tokens}")
                        
                    # Si no se encontraron códigos, salir
                    if not valid_tokens:
                        return
                        
                    # Procesar los códigos encontrados
                    sender_name = "tí" if event.sender_id == self.config.ADMIN_CHAT_ID else "un contacto"
                    self.log(f"📨 Mensaje de {sender_name} contiene códigos: {', '.join(valid_tokens)}")
                    
                    # Procesar cada token válido
                    for token in valid_tokens:
                        try:
                            # Verificar si el auto-claim está activado
                            if not self.auto_claim_active:
                                self.log(f"Auto-claim desactivado. Ignorando código {token}")
                                continue
                                
                            # Procesar el código
                            self.log(f"🔍 Procesando código: {token}")
                            
                            # Enviar confirmación al administrador
                            if event.sender_id != self.config.ADMIN_CHAT_ID:
                                await self.client.send_message(
                                    self.config.ADMIN_CHAT_ID,
                                    f"🔍 *Nuevo código detectado en un chat personal:*\n`{token}`\n\n¿Deseas reclamarlo? Envía /claim_{token}",
                                    parse_mode='md'
                                )
                            
                            # Procesar el código
                            await self.manipulator.main(token)
                            
                            # Pequeña pausa entre códigos para evitar saturación
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            error_msg = f"Error al procesar token {token}: {str(e)}"
                            self.log(error_msg, "error")
                            try:
                                await self.client.send_message(
                                    self.config.ADMIN_CHAT_ID,
                                    f"❌ {error_msg}",
                                    parse_mode='md'
                                )
                            except Exception as send_error:
                                self.log(f"No se pudo enviar mensaje de error: {str(send_error)}", "error")
                except Exception as e:
                    self.log(f"Error al procesar mensaje: {str(e)}", "error")
            
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

    async def setup_bot_commands(self):
        """Configura los comandos del bot en BotFather"""
        try:
            # Configurar comandos del bot
            commands = [
                ('start', 'Inicia el bot'),
                ('autoclaim', 'Activa/desactiva el reclamo automático'),
                ('logs', 'Muestra los registros recientes'),
                ('help', 'Muestra la ayuda'),
                ('stop_bot', 'Detiene el bot'),
                ('restart', 'Reinicia el bot')
            ]
            
            await self.client(functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code='es',
                commands=[types.BotCommand(command=cmd, description=desc) for cmd, desc in commands]
            ))
            custom_print("Comandos del bot configurados correctamente", "success")
        except Exception as e:
            custom_print(f"Error configurando comandos del bot: {e}", "error")

    def setup_command_handlers(self):
        """Configura los manejadores de comandos del bot."""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            """Maneja el comando /start"""
            # Verificar si el comando viene del administrador
            is_admin = event.sender_id == self.config.ADMIN_CHAT_ID
            
            # Activar el monitoreo si es el administrador
            if is_admin:
                self.is_monitoring_active = True
                self.chat_ids.add(event.chat_id)  # Agregar este chat a los monitoreados
                
            welcome_msg = """
🤖 *Bienvenido al Bot de Reclamo de Códigos Binance*

📝 *Comandos disponibles:*
/start - Muestra el mensaje de bienvenida
/autoclaim - Activa/desactiva el reclamo automático
/logs - Muestra los registros recientes
/help - Muestra la ayuda
/stop_bot - Detiene el bot
/restart - Reinicia el bot

📌 *Cómo usar:*
- Envía códigos de 8 caracteres para reclamarlos
- Ejemplo: `ABC123XY`

El bot está listo para usarse. ¡Empieza a reclamar códigos!"""
            await event.respond(welcome_msg, parse_mode='Markdown')

        @self.client.on(events.NewMessage(pattern='/autoclaim'))
        async def autoclaim_handler(event):
            """Maneja el comando /autoclaim"""
            # Verificar si el comando viene del administrador
            if event.sender_id != self.config.ADMIN_CHAT_ID:
                await event.respond("❌ Solo el administrador puede usar este comando.")
                return
                
            # Cambiar el estado de auto-claim
            self.auto_claim_active = not self.auto_claim_active
            status = "activado ✅" if self.auto_claim_active else "desactivado ⛔"
            
            # Si se activa el auto-claim, asegurarse de que el monitoreo también esté activo
            if self.auto_claim_active:
                self.is_monitoring_active = True
                self.chat_ids.add(event.chat_id)
                
                # Mensaje más detallado cuando se activa
                response = (
                    f"🚀 *RECLAMO AUTOMÁTICO ACTIVADO*\n\n"
                    f"🔍 El bot ahora buscará y canjeará automáticamente códigos en los mensajes.\n"
                    f"📡 Monitoreo de chats: ACTIVO\n"
                    f"👤 Chats monitoreados: {len(self.chat_ids)}"
                )
            else:
                # Mensaje cuando se desactiva
                response = (
                    f"⛔ *RECLAMO AUTOMÁTICO DESACTIVADO*\n\n"
                    f"El bot ya no canjeará códigos automáticamente.\n"
                    f"📡 Monitoreo de chats: {'ACTIVO' if self.is_monitoring_active else 'INACTIVO'}"
                )
                
            await event.respond(response, parse_mode='md')
            custom_print(f"Reclamo automático {status} por {event.sender_id}", "info")
            
            # Si se activó, enviar un mensaje de confirmación después de 2 segundos
            if self.auto_claim_active:
                await asyncio.sleep(2)
                await event.respond("🔍 *Modo Auto-Claim activo*\nAhora puedo detectar y canjear códigos automáticamente. Solo envíame los mensajes con códigos y yo me encargaré del resto. 😊", parse_mode='md')
            
        @self.client.on(events.NewMessage(pattern='/claim_([A-Z0-9]{8})'))
        async def claim_code_handler(event):
            """Maneja el comando para reclamar un código manualmente"""
            # Verificar si el comando viene del administrador
            if event.sender_id != self.config.ADMIN_CHAT_ID:
                await event.respond("❌ Solo el administrador puede usar este comando.")
                return
                
            # Extraer el código del comando
            code = event.pattern_match.group(1)
            
            if not code:
                await event.respond("❌ Formato de código inválido. Usa: /claim_CODIGO")
                return
                
            await event.respond(f"🔍 Intentando reclamar código: `{code}`", parse_mode='md')
            
            try:
                # Procesar el código
                await self.manipulator.main(code)
                await event.respond(f"✅ Código `{code}` procesado con éxito.", parse_mode='md')
            except Exception as e:
                error_msg = f"Error al procesar el código {code}: {str(e)}"
                custom_print(error_msg, "error")
                await event.respond(f"❌ {error_msg}")

        @self.client.on(events.NewMessage(pattern='/logs'))
        async def logs_handler(event):
            """Maneja el comando /logs"""
            # Aquí puedes implementar la lógica para mostrar logs
            await event.respond("📜 Mostrando últimos registros... (función en desarrollo)")

        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_command(event):
            """Muestra los comandos disponibles"""
            help_text = (
                "🤖 *Comandos disponibles:*\n\n"
                "• /start - Iniciar el bot\n"
                "• /autoclaim - Activar/desactivar el canje automático\n"
                "• /resumen - Muestra resumen de códigos canjeados\n"
                "• /stop_bot - Detener el bot\n"
                "• /restart - Reiniciar el bot\n"
                "• /help - Muestra este mensaje de ayuda"
            )
            await event.respond(help_text, parse_mode='markdown')
            
        @self.client.on(events.NewMessage(pattern='/resumen'))
        async def summary_command(event):
            """Muestra un resumen de los códigos canjeados"""
            if event.sender_id != self.config.ADMIN_CHAT_ID:
                await event.respond("❌ Solo el administrador puede ver el resumen.")
                return
                
            summary = await self.manipulator.get_claim_summary()
            await event.respond(summary, parse_mode='markdown')
            
        # Manejador para códigos en mensajes
        @self.client.on(events.NewMessage())
        async def message_handler(event):
            """Maneja los mensajes que contienen códigos"""
            if not self.is_monitoring_active:
                return
                
            # Buscar códigos en el mensaje
            message_text = event.raw_text.strip()
            tokens = re.findall(r'\b(?!\d+\b)(?![a-z]+\b)[A-Z0-9]{8}\b', message_text.upper())
            
            # Si se encontraron códigos válidos, procesarlos
            for token in tokens:
                custom_print(f"Código detectado: {token}", "info")
                await self.manipulator.main(token)
                
                # Notificar al usuario
                if event.is_private:
                    await event.respond(f"✅ Código procesado: `{token}`", parse_mode='Markdown')

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
        self.log("Iniciando el bot...", "info")
        
        # Inicializar el cliente de Telegram
        if not hasattr(self, 'client') or not self.client:
            if not self.initialize_client():
                self.log("No se pudo inicializar el cliente de Telegram", "error")
                return
                
        try:
            self.log("Conectando al servidor de Telegram...", "info")
            self.client.loop.run_until_complete(self.start_client())
            self.client.run_until_disconnected()
        except KeyboardInterrupt:
            self.log("Bot detenido por el usuario", "info")
        except Exception as e:
            self.log(f"Error durante la ejecución del bot: {str(e)}", "error")
        finally:
            self.log("Desconectando el bot...", "info")
            self.client.disconnect()
