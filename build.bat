@echo off
echo Building VPN Checker portable exe...
call .venv\Scripts\activate
pyinstaller --onefile --windowed --name VPN-Checker ^
  --add-data "services.json;." ^
  main.py
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
