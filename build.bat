@echo off
echo Building VPN Checker portable exe...
uv sync --extra build
uv run pyinstaller VPN-Checker.spec --noconfirm
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
