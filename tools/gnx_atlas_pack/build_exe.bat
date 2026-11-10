@echo off
echo Building gnx_atlas_pack.exe...
python -m pip install --quiet pyinstaller Pillow
pyinstaller --onefile --name gnx_atlas_pack gnx_atlas_pack.py
echo.
echo Result: dist\gnx_atlas_pack.exe
pause
