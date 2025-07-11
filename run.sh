#!/bin/bash

# Script de lancement du Générateur de Spin Content
# Utilise Python 3.12 avec Streamlit installé

echo "🚀 Lancement du Générateur de Spin Content..."

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Créez-le avec :"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Lancer Streamlit avec Python 3.12
./venv/bin/python3.12 -m streamlit run spin_generator.py

echo "✅ Application fermée" 