@echo off
echo Installing DPMS...

python -m pip install --upgrade pip
python -m pip install -e .

echo Done. You can now run: dpms
pause
