@echo off
setlocal

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed or not in PATH.
  pause
  exit /b 1
)

echo [2/4] Installing/Upgrading PyInstaller...
python -m pip install --upgrade pip pyinstaller

echo [3/4] Building EXE...
pyinstaller --onefile --name Ashamy main.py

echo [4/4] Done.
echo EXE path: dist\Ashamy.exe
pause
