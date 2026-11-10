@echo off
echo Installing gnx-atlas-pack dependencies...
python -m pip install --upgrade pip
python -m pip install Pillow
echo.
echo Optional: build standalone .exe
echo   python -m pip install pyinstaller
echo   pyinstaller --onefile gnx_atlas_pack.py
pause
