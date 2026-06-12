@echo off
setlocal

echo 🚀 Lancement du Générateur de Spin Content...

if not exist "venv\Scripts\python.exe" (
    echo 📦 Environnement virtuel introuvable, création en cours...
    where py >nul 2>&1
    if %errorlevel%==0 (
        py -3.11 -m venv venv >nul 2>&1
        if %errorlevel% neq 0 py -3 -m venv venv
    ) else (
        python -m venv venv
    )

    if %errorlevel% neq 0 (
        echo ❌ Python 3.11+ est requis pour lancer l'application.
        exit /b 1
    )
)

venv\Scripts\python.exe -c "import streamlit, pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installation des dépendances...
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 exit /b 1
)

venv\Scripts\python.exe -m streamlit run spin_generator.py --server.headless true --server.port 8501
