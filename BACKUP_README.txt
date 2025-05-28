# 📦 Respaldo de Configuración - Bot Binance

Este archivo contiene información importante sobre la configuración actual del bot.

## 🔑 Datos Importantes
- Última actualización: 28/05/2025 01:03 AM
- Versión estable: v2.0.0
- Compatible con Python 3.8+

## ⚙️ Configuración Actual

### Configuración de Telegram
- API_ID: [TU_API_ID]
- API_HASH: [TU_API_HASH]
- CLIENT_NAME: binance_bot

### Configuración de Binance
- URL de la API: https://www.binance.com/bapi/pay/v1/private/binance-pay/gift-box/code/grabV2
- Headers configurados: Sí
- Límite de solicitudes/hora: 50

## 📂 Archivos Importantes
- `main.py`: Punto de entrada principal
- `lib/api/telegram.py`: Lógica del cliente de Telegram
- `lib/api/binance.py`: Lógica de la API de Binance
- `lib/manipulator.py`: Procesamiento de códigos
- `source/config.py`: Configuración del bot

## 🔄 Cómo restaurar
1. Asegúrate de tener Python 3.8+ instalado
2. Instala las dependencias: `pip install -r requirements.txt`
3. Configura tus credenciales en `source/config.py`
4. Ejecuta: `python main.py`

## 📝 Notas
- Los códigos deben tener 8 caracteres alfanuméricos en mayúsculas
- El bot ignora automáticamente mensajes que no contengan códigos válidos
- Se recomienda monitorear el bot periódicamente

## 📞 Soporte
Si necesitas ayuda, revisa el README.md o abre un issue en el repositorio.
