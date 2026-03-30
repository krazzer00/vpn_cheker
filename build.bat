@echo off
echo Building VPN Checker portable exe...
uv sync --extra build
uv run pyinstaller --onefile --windowed --name VPN-Checker ^
  --add-data "services.json;." ^
  --icon icon.ico ^
  main.py
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
