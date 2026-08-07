#!/usr/bin/env bash
set -euo pipefail

# Se placer dans le dossier du script, peu importe d'où il est appelé
cd "$(dirname "${BASH_SOURCE[0]}")"

# Vérifie qu'au moins un moyen d'exécuter le script Python est disponible
if ! command -v uv > /dev/null && ! command -v python3 > /dev/null; then
    echo "Erreur : ni 'uv' ni 'python3' trouvés dans le PATH." >&2
    echo "Installe uv (https://docs.astral.sh/uv/) ou Python 3." >&2
    exit 1
fi

# Détermine le script à lancer : gestion des tickers si arguments fournis,
# sinon lancement du widget (comportement par défaut)
if [ "$#" -gt 0 ]; then
    TARGET="cli.py"
else
    TARGET="main.py"
    clear
fi

if command -v uv > /dev/null; then
    uv run "$TARGET" "$@"
else
    if [ ! -d ".venv" ]; then
        echo "Erreur : .venv introuvable et 'uv' non disponible." >&2
        echo "Crée le venv manuellement : python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
        exit 1
    fi
    source .venv/bin/activate
    # utilise un CLI python pour l'installation (convertie les tickers EURONEXT en yfinance)
    python3 "$TARGET" "$@"
fi