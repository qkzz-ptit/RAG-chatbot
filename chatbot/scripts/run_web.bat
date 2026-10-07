@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\activate.bat" (
    echo Chua co moi truong Python .venv. Hay lam theo phan Cai dat trong README.md.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m streamlit run app.py
pause
