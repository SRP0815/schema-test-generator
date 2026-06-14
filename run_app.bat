@echo off
set "PROJECT_DIR=%~dp0"
set "APP_FILE=%PROJECT_DIR%app.py"

cd /d "%PROJECT_DIR%"
python -m streamlit run "%APP_FILE%" --server.port 8501
