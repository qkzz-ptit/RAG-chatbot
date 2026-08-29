@echo off
cd /d C:\chatbot
call .venv\Scripts\activate
streamlit run app.py
pause