"""
CLI Python pour gérer la liste de tickers suivis par le widget.
Fait la conversion ticker EURONEXT -> symbole yfinance via un fichier maison.
"""

import sys
import json
from pathlib import Path

from main import CONFIG_PATH, load_config

SCRIPT_DIR = Path(__file__).parent
KNOWN_TICKERS_PATH = SCRIPT_DIR / "actions_connues.json"

MODES = ["-a", "--add", "-r", "--remove", "-m", "--modify", "-h", "--help", "-s", "--sort"]

def print_help(mode: str = "") -> None:
    if mode == "":
        print("=" * 10, "Aide", "=" * 10)
        print("Usage: stocks [commande] [ticker...]")
        print("Commandes disponibles :")
        print()
        for m in MODES:
            print(f"--> {m}")
    elif mode in ("-a", "--add"):
        print("Usage: stocks -a/--add TICKER[:Label[:PRU[:Quantity]]] ...")
    elif mode in ("-r", "--remove"):
        print("Usage: stocks -r/--remove TICKER [TICKER ...]")
    elif mode in ("-m", "--modify"):
        print("Usage: stocks -m/--modify TICKER[:Label[:PRU[:Quantity]]] ...")
        print("Permet de modifier le PRU et/ou la quantité d'un ticker existant.")
    elif mode in ("-s", "--sort"):
        print("Usage: ./run.sh run --sort -c|-d|-vc|-vd|-ac|-ad")

def load_known_tickers() -> dict:
    """Charge le fichier de conversion EURONEXT -> yfinance en une seule lecture."""
    if not KNOWN_TICKERS_PATH.exists():
        print(f"Erreur : {KNOWN_TICKERS_PATH} introuvable.")
        sys.exit(1)

    with open(KNOWN_TICKERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_ticker(euronext_ticker: str, known: dict) -> str | None:
    """Retourne le symbole yfinance correspondant en mémoire (zéro accès disque)."""
    for category in ("actions", "etf"):
        for item in known[category]:
            if item["symbol"] == euronext_ticker:
                return item["symbol"]
    return None

def save_config(config: dict) -> None:
    """Sauvegarde la configuration en une seule écriture."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def modify_pru_quantity(euronext_ticker: str, new_pru: float | None = None, new_quantity: int | None = None) -> bool:
    """
    Modifie le PRU et/ou la quantité d'un ticker suivi dans tickers.json.
    
    Optimisations :
    - Effectue exactement 1 seule lecture de `tickers.json` et 1 seule lecture de `actions_connues.json`.
    - Permet une mise à jour partielle : si new_pru ou new_quantity est None, la valeur existante est conservée.
    """
    # 1. Chargement unique des données nécessaires
    config = load_config()
    known = load_known_tickers()
    
    # Résolution du symbole en mémoire
    symbol = resolve_ticker(euronext_ticker, known)
    if symbol is None:
        # Fallback si le ticker passé est déjà le symbole direct
        symbol = euronext_ticker

    ticker_found = False
    changes = []

    # 2. Parcours en mémoire de la liste des tickers suivis
    for entry in config["tickers"]:
        if entry["symbol"] == symbol or entry.get("label") == euronext_ticker:
            ticker_found = True
            
            # Mise à jour conditionnelle du PRU
            if new_pru is not None:
                old_pru = entry.get("pru")
                entry["pru"] = new_pru
                changes.append(f"PRU ({old_pru} → {new_pru})")
                
            # Mise à jour conditionnelle de la quantité
            if new_quantity is not None:
                old_qty = entry.get("quantity")
                entry["quantity"] = new_quantity
                changes.append(f"Quantité ({old_qty} → {new_quantity})")
            
            break

    if not ticker_found:
        print(f"Erreur : Le ticker '{euronext_ticker}' (résolu en '{symbol}') n'est pas dans la liste suivie.")
        return False

    if not changes:
        print(f"Aucune modification n'a été spécifiée pour {symbol} (PRU et Quantité inchangés).")
        return False

    # 3. Sauvegarde unique sur disque
    save_config(config)
    print(f"Mise à jour réussie pour {symbol} -> {', '.join(changes)}.")
    return True


def parse_ticker_arg(arg: str, known: dict | None = None) -> tuple[str, str | None, float | None, int | None]:
    """
    Découpe un argument au format : TICKER[:Label[:PRU[:Quantity]]]
    Accepte un dictionnaire `known` optionnel pour éviter de recharger le fichier.
    """
    parts = arg.split(":", 3)
    ticker = parts[0].strip()

    if known is None:
        known = load_known_tickers()

    label = None
    pru = None
    quantity = None

    known_item = next(
        (
            item for item in known.get("actions", []) + known.get("etf", [])
            if item["symbol"] == ticker
        ),
        None
    )
    known_label = known_item["label"] if known_item else None

    if len(parts) >= 2:
        label = parts[1].strip() or known_label

    if len(parts) >= 3 and parts[2].strip():
        pru = float(parts[2].strip())

    if len(parts) >= 4 and parts[3].strip():
        quantity = int(parts[3].strip())

    return ticker, label, pru, quantity


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print_help()
        sys.exit(0)

    mode = args[0]

    if mode not in MODES:
        print(f"{mode}: commande non reconnue.")
        print_help()
        sys.exit(1)

    if mode in ("-h", "--help"):
        if len(args) > 1: print_help(args[1])
        else: print_help("")
        sys.exit(0)

    raw_tickers = args[1:]
    if not raw_tickers:
        print("Aucun ticker fourni.")
        print_help(mode)
        sys.exit(1)

    # Chargement mutualisé des actions connues pour la boucle principale
    known = load_known_tickers()

    if mode in ("-a", "--add"):
        config = load_config() # Chargement unique pour les ajouts multiples en lot
        for raw in raw_tickers:
            ticker, label, pru, quantity = parse_ticker_arg(raw, known)
            # (Logique d'ajout adaptée si besoin...)
    elif mode in ("-r", "--remove"):
        for raw in raw_tickers:
            ticker, _, _, _ = parse_ticker_arg(raw, known)
            # remove(ticker)
    elif mode in ("-m", "--modify"):
        for raw in raw_tickers:
            ticker, _, pru, qty = parse_ticker_arg(raw, known)
            modify_pru_quantity(ticker, new_pru=pru, new_quantity=qty)


if __name__ == "__main__":
    main()