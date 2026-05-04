@echo off
cd /d "%~dp0"

call venv\Scripts\activate.bat

set BROWSER=none
streamlit run ui\streamlit_app\app.py --server.headless true

pause