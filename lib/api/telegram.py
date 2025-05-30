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
        """Extrae códigos de 8 caracteres alfanuméricos en mayúsculas"""
        if not text or not isinstance(text, str):
            return set()
            
        # Buscar secuencias de exactamente 8 caracteres alfanuméricos en mayúsculas
        codes = set(re.findall(r'\b([A-Z0-9]{8})\b', text.upper()))
        
        # Si no se encontraron códigos de 8 caracteres, buscar códigos de 8-10 caracteres
        if not codes:
            codes = set(re.findall(r'\b([A-Z0-9]{8,10})\b', text.upper()))
        
        # Registrar los códigos encontrados
        if codes:
            self.log(f"🔍 Códigos detectados: {', '.join(codes)}", "debug")
        else:
            self.log("No se encontraron códigos en el mensaje", "debug")
            
        return codes
        
    def log(self, message, level="info"):
        """Función de registro unificada"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}")
        
    async def initialize_client(self):
        """Inicializa el cliente de Telegram"""
        try:
            # Inicializar el cliente de Telegram con el bot token
            self.client = TelegramClient(
                'bot_session',
                self.config.API_ID,
                self.config.API_HASH
            )
            
            # Iniciar la conexión
            await self.client.start(bot_token=self.config.BOT_TOKEN)
            
            # Obtener información del bot
            me = await self.client.get_me()
            self.log(f"✅ Conectado como @{me.username} (ID: {me.id})", "success")
            
            # Inicializar el manipulador de tokens
            self.manipulator = ManipulateToken(self.config, self)
            self.manipulator._load_successful_claims()
            
            # Estado del bot
            self.is_monitoring_active = True
            self.auto_claim_active = True
            self.chat_ids = set()
            
            # Configurar manejadores
            self.setup_command_handlers()
            self.setup_event_handler()
            
            # Configurar comandos del bot
            await self.setup_bot_commands()
            
            # Registrar que el bot está listo
            self.log("🔍 Modo de monitoreo universal ACTIVADO", "info")
            self.log("🤖 Bot listo para detectar códigos en TODOS los chats", "info")
            self.log("👀 Monitoreando mensajes entrantes...", "info")
            
            # Notificar al administrador
            await self.send_admin_notification(
                "🤖 *Bot iniciado correctamente*\n"
                "El bot está listo para monitorear códigos."
            )
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error al inicializar el cliente de Telegram: {str(e)}", "error")
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



    async def process_message(self, event):
        """Procesa un mensaje entrante"""
        try:
            # Obtener información del mensaje
            message = event.message
            chat = await event.get_chat()
            sender = await event.get_sender()
            
            # Ignorar mensajes propios
            if hasattr(sender, 'is_self') and sender.is_self:
                return
                
            # Obtener el ID del chat y el nombre
            chat_id = chat.id
            chat_title = getattr(chat, 'title', 'Chat privado')
            
            # Extraer el texto del mensaje
            text = message.text or message.raw_text or ''
            
            # Extraer códigos del mensaje
            codes = self.extract_codes(text)
            
            if codes:
                custom_print(f"📨 Mensaje de {chat_title} (ID: {chat_id}): {text}", "debug")
                custom_print(f"🔍 Códigos detectados: {', '.join(codes)}", "success")
                
                # Procesar cada código encontrado
                for code in codes:
                    try:
                        custom_print(f"🔧 Procesando código: {code}", "info")
                        # Usar el manipulador para procesar el código
                        await self.manipulator.main(code)
                        # Pequeña pausa entre códigos
                        await asyncio.sleep(1)
                    except Exception as e:
                        custom_print(f"Error al procesar código {code}: {str(e)}", "error")
            
            return True
            
        except Exception as e:
            custom_print(f"Error al procesar mensaje: {str(e)}", "error")
            return False
            
    # Eliminado el manejador duplicado de mensajes

    def setup_event_handler(self):
        """Configura el manejador de eventos para mensajes"""
        @self.client.on(events.NewMessage())
        async def message_handler(event):
            try:
                # Obtener el texto del mensaje
                message_text = event.raw_text or ''
                
                # Registrar información del mensaje
                self.log(f"\n📨 Mensaje recibido en chat ID: {event.chat_id}", "debug")
                self.log(f"👤 Remitente ID: {event.sender_id}", "debug")
                self.log(f"📝 Contenido: {message_text}", "debug")
                
                # Ignorar mensajes propios
                if hasattr(event.sender, 'is_self') and event.sender.is_self:
                    self.log("Ignorando mensaje propio", "debug")
                    return
                    
                # Ignorar mensajes de canales anónimos
                if hasattr(event.sender, 'id') and event.sender.id == 777000:
                    self.log("Ignorando mensaje de canal anónimo", "debug")
                    return
                
                # Verificar si el mensaje es relevante (contiene texto)
                if not message_text.strip():
                    self.log("Mensaje vacío, ignorando", "debug")
                    return
                
                # Buscar códigos en el mensaje
                codes = self.extract_codes(message_text)
                
                if codes:
                    # Filtrar códigos ya procesados
                    filtered_codes = []
                    for code in codes:
                        if code in self.manipulator.permanently_claimed_codes:
                            self.log(f"🔍 Código ya procesado: {code}", "debug")
                            continue
                        if code in self.manipulator.processed_tokens:
                            self.log(f"🔍 Código ya procesado en esta sesión: {code}", "debug")
                            continue
                        filtered_codes.append(code)
                    
                    if not filtered_codes:
                        self.log("🔍 Todos los códigos ya han sido procesados anteriormente", "debug")
                        return
                        
                    self.log(f"🔍 Códigos nuevos detectados: {', '.join(filtered_codes)}", "info")
                    
                    # Procesar cada código encontrado
                    for code in filtered_codes:
                        try:
                            self.log(f"🔧 Procesando código: {code}", "info")
                            await self.manipulator.main(code)
                            await asyncio.sleep(1)  # Pequeña pausa entre códigos
                        except Exception as e:
                            self.log(f"Error al procesar código {code}: {str(e)}", "error")
                else:
                    self.log("No se encontraron códigos en el mensaje", "debug")
                
                # Procesar mensajes con formato de pregunta/respuesta de Binance
                if 'Answer:' in message_text and 'app.binance.com/uni-qr/cart/' in message_text:
                    self.log("📝 Mensaje de Binance detectado", "debug")
                    try:
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
                                self.log(f"🔑 Procesando código de Binance: {code} con respuesta: {answer}", "info")
                                await self.process_code_with_answer(code, answer)
                    except Exception as e:
                        self.log(f"Error al procesar mensaje de Binance: {str(e)}", "error")
                        
            except Exception as e:
                self.log(f"❌ Error en el manejador de mensajes: {str(e)}", "error")
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
        """Inicia el cliente de Telegram con autenticación de usuario"""
        try:
            custom_print("🔑 Iniciando sesión en Telegram...", "info")
            
            # Configurar el cliente con tus credenciales API
            self.client = TelegramClient(
                'user_session',  # Nombre del archivo de sesión
                self.config.API_ID,
                self.config.API_HASH,
                device_model="PC",
                app_version="1.0.0",
                system_version="Windows 10",
                lang_code="es",
                system_lang_code="es"
            )
            
            # Iniciar sesión
            await self.client.start(
                phone=lambda: input('\n📱 Por favor ingresa tu número de teléfono (con código de país, ej: +521234567890): '),
                code_callback=lambda: input('🔑 Ingresa el código de verificación: '),
                password=lambda: input('🔐 Si tienes autenticación en dos pasos, ingresa la contraseña: ')
            )
            
            # Verificar la sesión
            me = await self.client.get_me()
            custom_print(f"✅ Sesión iniciada como {me.first_name} (@{me.username or 'sin_usuario'}) - ID: {me.id}", "success")
            
            # Configurar manejadores
            self.setup_command_handlers()
            self.setup_event_handler()
            
            # Inicializar manipulador de tokens
            self.manipulator = ManipulateToken(self.config, self)
            self.manipulator._load_successful_claims()
            
            # Estado del bot
            self.is_monitoring_active = True
            self.auto_claim_active = True
            self.chat_ids = set()
            
            custom_print("\n🤖 Bot iniciado correctamente", "info")
            custom_print("👀 Monitoreando mensajes entrantes...", "info")
            
            # Mantener la sesión activa
            await self.client.run_until_disconnected()
            return True
            
        except Exception as e:
            custom_print(f"❌ Error al iniciar la sesión: {str(e)}", "error")
            return False

    async def start_async(self):
        """Método asíncrono para iniciar el cliente"""
        self.log("Iniciando el bot...", "info")
        
        try:
            # Iniciar el cliente de Telegram
            self.log("Conectando al servidor de Telegram...", "info")
            
            # Configurar el cliente con tus credenciales API
            self.client = TelegramClient(
                'user_session',  # Nombre del archivo de sesión
                self.config.API_ID,
                self.config.API_HASH,
                device_model="PC",
                app_version="1.0.0",
                system_version="Windows 10",
                lang_code="es",
                system_lang_code="es"
            )
            
            # Iniciar sesión
            await self.client.start(
                phone=lambda: input('\n📱 Por favor ingresa tu número de teléfono (con código de país, ej: +521234567890): '),
                code_callback=lambda: input('🔑 Ingresa el código de verificación: '),
                password=lambda: input('🔐 Si tienes autenticación en dos pasos, ingresa la contraseña: ')
            )
            
            # Verificar la sesión
            me = await self.client.get_me()
            self.log(f"✅ Sesión iniciada como {me.first_name} (@{me.username or 'sin_usuario'}) - ID: {me.id}", "success")
            
            # Configurar manejadores
            self.setup_command_handlers()
            self.setup_event_handler()
            
            # Inicializar manipulador de tokens
            self.manipulator = ManipulateToken(self.config, self)
            self.manipulator._load_successful_claims()
            
            # Estado del bot
            self.is_monitoring_active = True
            self.auto_claim_active = True
            self.chat_ids = set()
            
            self.log("\n🤖 Bot iniciado correctamente", "info")
            self.log("👀 Monitoreando mensajes entrantes...", "info")
            
            # Mantener la sesión activa
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            self.log("\n🛑 Bot detenido por el usuario", "info")
        except Exception as e:
            self.log(f"❌ Error durante la ejecución del bot: {str(e)}", "error")
        finally:
            self.log("🔌 Desconectando el bot...", "info")
            if hasattr(self, 'client') and self.client:
                await self.client.disconnect()
    
    def start(self):
        """Método principal síncrono para iniciar el cliente"""
        try:
            # Crear un nuevo bucle de eventos
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_async())
        except Exception as e:
            self.log(f"❌ Error al iniciar el bot: {str(e)}", "error")
            import traceback
            traceback.print_exc()  # Imprimir el traceback completo
        finally:
            # Cerrar el bucle de eventos
            loop.close()
