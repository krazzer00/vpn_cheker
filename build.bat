@echo off
echo Building VPN Checker portable exe...
call .venv\Scripts\activate
pyinstaller --onefile --windowed --name VPN-Checker ^
  --add-data "services.json;." ^
  --icon icon.ico ^
  --hidden-import PIL ^
  --hidden-import PIL._imagingtk ^
  main.py
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
