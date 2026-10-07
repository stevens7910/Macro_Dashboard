@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Cesky Makroekonomicky Dashboard

cd /d "%~dp0"
echo ========================================================
echo  Spoustim Cesky Makroekonomicky Dashboard ve Streamlit...
echo ========================================================
echo.

if exist "C:\Users\steve\.local\bin\uv.exe" (
    "C:\Users\steve\.local\bin\uv.exe" run --with-requirements requirements.txt streamlit run app.py
) else (
    python -m streamlit run app.py
)

if %errorlevel% neq 0 (
    echo.
    echo Doslo k chybe pri spousteni.
    pause
)
