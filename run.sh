#!/usr/bin/env bash

set -euo pipefail

# Script de lancement robuste pour macOS/Linux.

echo "🚀 Lancement du Générateur de Spin Content..."

if [ ! -x "venv/bin/python" ]; then
    echo "📦 Environnement virtuel introuvable, création en cours..."

    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_BIN="python3.11"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "❌ Python 3.11+ est requis pour lancer l'application."
        exit 1
    fi

    "$PYTHON_BIN" -m venv venv
fi

if ! ./venv/bin/python - <<'PY' >/dev/null 2>&1
import pandas  # noqa: F401
import streamlit  # noqa: F401
PY
then
    echo "📥 Installation des dépendances..."
    ./venv/bin/python -m pip install -r requirements.txt
fi

exec ./venv/bin/python -m streamlit run spin_generator.py --server.headless true --server.port 8501
