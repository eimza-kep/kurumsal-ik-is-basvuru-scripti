@echo off
chcp 65001 >nul
echo =================================================================
echo        KURUMSAL İK & İŞ BAŞVURU SİSTEMİ BAŞLATICI
echo =================================================================
echo.
echo Sunucu hazırlanıyor ve başlatılıyor...
echo Port: 8084
echo.
start "" http://localhost:8084
python server.py
pause
