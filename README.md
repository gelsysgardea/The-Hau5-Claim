# 🏠 The Hau5 Claim 🤖

Herramienta automatizada para reclamar códigos de criptocajas de Binance desde canales de Telegram.

> ⚠️ **IMPORTANTE**: Este bot es solo para uso personal. Úsalo bajo tu propio riesgo y asegúrate de cumplir con los Términos de Servicio de Binance.

## 📋 Requisitos Previos

- Python 3.8 o superior
- Cuenta de Telegram
- Cuenta de Binance verificada

## 🛠️ Instalación Segura

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/tu-usuario/Binance-Crypto-Box-Wrapper
   cd Binance-Crypto-Box-Wrapper
   ```

2. **Crear un entorno virtual (recomendado)**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # En Windows
   # O en Linux/Mac: source .venv/bin/activate
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuración Inicial**

   - Copia el archivo `source/config.example.py` a `source/config.py`

     ```bash
     copy source\config.example.py source\config.py
     ```

   - Sigue las instrucciones en el archivo `source/config.py` para configurar tus credenciales

## 🔒 Configuración Segura

### 1. Obtener credenciales de Telegram
1. Ve a [my.telegram.org](https://my.telegram.org/)
2. Inicia sesión con tu cuenta de Telegram
3. Crea una nueva aplicación o usa una existente
4. Copia el `api_id` y `api_hash`

### 2. Configurar el archivo `source/config.py`

```python
# Configuración de Telegram
API_ID = 1234567  # Reemplaza con tu API ID
API_HASH = "tu_api_hash_aquí"  # Reemplaza con tu API HASH
CLIENT_NAME = "binance_bot"  # Puedes dejarlo así o cambiarlo

# Configuración del bot
MAX_HOUR_REQUESTS = 50  # Límite de solicitudes por hora (0 para ilimitado)
EXCLUDE_CHATS_WITH = ["intel"]  # Palabras para excluir chats
```

### 3. Configuración de Binance
1. Inicia sesión en tu cuenta de Binance
2. Abre las herramientas de desarrollo del navegador (F12)
3. Ve a la pestaña "Red" (Network)
4. Navega a la sección de Crypto Box
5. Copia los headers necesarios (especialmente User-Agent y cookies)

## 🚀 Uso del Bot

1. **Iniciar el bot**

   ```bash
   python main.py
   ```

2. **Primera ejecución**
   - La primera vez que ejecutes el bot, se te pedirá que inicies sesión en Telegram
   - Sigue las instrucciones en la consola
   - Se creará un archivo de sesión (no lo compartas con nadie)

3. **Uso normal**
   - El bot se ejecutará en segundo plano
   - Monitoreará automáticamente los canales configurados
   - Reclamará los códigos de forma automática

## ⚠️ Seguridad

- **NUNCA** compartas tus credenciales de API ni archivos de sesión
- Usa un entorno virtual para aislar las dependencias
- Revisa regularmente los permisos de tus aplicaciones en Telegram
- Considera usar una cuenta de Telegram separada para el bot

## 📝 Notas

- El bot está configurado para evitar solicitudes excesivas a los servidores de Binance
- Los códigos reclamados se guardan en `data/claimed_codes.json`
- Revisa los logs en la consola para ver la actividad del bot
   ```bash
   python main.py
   ```

2. **Iniciar sesión en Telegram**

   - El bot te pedirá que ingreses tu número de teléfono
   - Proporciona el código de verificación que recibas

3. **Monitoreo automático**

   El bot comenzará a monitorear automáticamente los chats en busca de códigos de Binance.

## 🔍 Características

- 🎯 Detección inteligente de códigos de Binance
- ⏱️ Retraso configurable entre solicitudes para evitar baneos
- 📊 Registro detallado de actividades
- 🔄 Reintentos automáticos en caso de errores
- 🛡️ Manejo seguro de credenciales

## ⚠️ Precauciones

- No compartas tus credenciales de API ni cookies de sesión
- El bot incluye un límite de solicitudes por hora para evitar baneos
- Úsalo bajo tu propio riesgo

## 📝 Notas

- Los códigos deben tener 8 caracteres alfanuméricos en mayúsculas
- El bot ignorará automáticamente mensajes que no contengan códigos válidos
- Se recomienda monitorear el bot periódicamente

## 📄 Licencia

MIT License - Usa bajo tu propia responsabilidad
