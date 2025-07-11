@echo off
echo 🚀 Lancement du Générateur de Spin Content...

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo ❌ Environnement virtuel non trouvé. Créez-le avec :
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)

REM Lancer Streamlit
venv\Scripts\python.exe -m streamlit run spin_generator.py

echo ✅ Application fermée
pause 