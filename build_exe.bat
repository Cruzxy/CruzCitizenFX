@echo off
title Build - FiveM Token Extractor
echo [*] Instalando dependencias...
pip install pyshark requests colorama pyinstaller psutil

echo.
echo [*] Gerando executavel...
pyinstaller --onefile --noconsole --name "FivemTokenExtractor" fivem_token_extractor.py

echo.
echo [OK] Pronto! O .exe esta em: dist\FivemTokenExtractor.exe
pause
