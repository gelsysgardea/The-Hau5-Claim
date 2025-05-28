@echo off
title Binance Crypto Box Wrapper - Configurador Personal

:: 1. Verificaciones iniciales (Python/pip)
python --version >nul 2>&1 || (
   echo [ERROR] Python no encontrado en el PATH
   pause
   exit /b
)

python -m pip --version >nul 2>&1 || (
   echo [ERROR] Pip no instalado. Ejecuta:
   echo         python -m ensurepip --upgrade
   pause
   exit /b
)

:: 2. Instalar/actualizar dependencias
echo [✓] Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install telethon aiohttp
if %errorlevel% neq 0 (
   echo [ERROR] Fallo al instalar dependencias
   pause
   exit /b
)

:: 3. Crear script temporal para detectar grupos
set "temp_script=%temp%\detect_groups.py"
(
echo import asyncio
echo from telethon.sync import TelegramClient
echo from telethon.tl.functions.messages import GetDialogsRequest
echo from telethon.tl.types import InputPeerEmpty
echo
echo async def main():
echo     async with TelegramClient('session_name', %api_id%, '%api_hash%') as client:
echo         result = await client(GetDialogsRequest(
echo             offset_date=None,
echo             offset_id=0,
echo             offset_peer=InputPeerEmpty(),
echo             limit=200,
echo             hash=0
echo         ))
echo         groups = [chat.id for chat in result.chats if hasattr(chat, 'megagroup') and chat.megagroup]
echo         print("CHATS_DETECTADOS=" ^+ "^,".join(map(str, groups)) ^+ "^")
echo
echo asyncio.run(main())
) > "%temp_script%"

:: 4. Configuración interactiva
:credentials
echo.
echo [CONFIGURACION] Ingresa tus credenciales PERSONALES:
echo ---------------------------------------------------
set /p "api_id=API_ID (de TU cuenta): "
set /p "api_hash=API_HASH: "
set /p "phone=Tu número (ej. +521234567890): "

:: 5. Detectar grupos automáticamente
echo.
echo [✓] Detectando tus grupos (esto puede tomar unos segundos)...
for /f "tokens=*" %%a in ('python "%temp_script%"') do set "output=%%a"
del "%temp_script%"

:: 6. Generar config.py con tus grupos
echo.
echo [✓] Generando config.py personalizado...
(
echo from dataclasses import dataclass
echo from typing import Union
echo.
echo @dataclass
echo class Config:
echo     CHATS = [%output:CHATS_DETECTADOS=%]
echo     CLIENT_NAME = "SesionPersonal"
echo     API_ID = %api_id%
echo     API_HASH = "%api_hash%"
echo     PHONE = "%phone%"
) > source\config.py

:: 7. Iniciar
echo.
echo [✓] Configuración completada. Iniciando...
python main.py
pause