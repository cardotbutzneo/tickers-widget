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

MODES = ["-a", "--add", "-r", "--remove", "-h", "--help"]

def print_help(mode: str = "") -> None:
    if mode == "":
        print("=" * 10, "Aide", "=" * 10)
        print("Usage: stocks [commande] [ticker...]")
        print("Commandes disponibles :")
        print()
        for m in MODES:
            print(f"--> {m}")
    elif mode in ("-a", "--add"):
        print("Usage: stocks -a/--add TICKER[:Label] [TICKER[:Label] ...]")
        print("Ticker au format EURONEXT (ex: RMS, OR).")
        print("Label optionnel après ':' (ex: RMS:Hermès). Par défaut, le ticker EURONEXT est utilisé.")
    elif mode in ("-r", "--remove"):
        print("Usage: stocks -r/--remove TICKER [TICKER ...]")


def load_known_tickers() -> dict:
    """Charge le fichier de conversion EURONEXT -> yfinance."""
    if not KNOWN_TICKERS_PATH.exists():
        print(f"Erreur : {KNOWN_TICKERS_PATH} introuvable.")
        sys.exit(1)

    with open(KNOWN_TICKERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_ticker(euronext_ticker: str, known: dict) -> str | None:
    """Retourne le symbole yfinance correspondant, ou None si inconnu."""
    for category in ("actions", "etf"):
        if euronext_ticker in known.get(category, {}):
            return known[category][euronext_ticker]
    return None


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def add(euronext_ticker: str, label: str | None = None) -> bool:
    """Ajoute un ticker (format EURONEXT) à tickers.json."""
    known = load_known_tickers()
    symbol = resolve_ticker(euronext_ticker, known)

    if symbol is None:
        print(f"Ticker non reconnu : {euronext_ticker}. Vérifiez {KNOWN_TICKERS_PATH.name}.")
        return False

    config = load_config()

    if any(t["symbole"] == symbol for t in config["tickers"]):
        print(f"{euronext_ticker} ({symbol}) est déjà suivi.")
        return False

    config["tickers"].append({"symbole": symbol, "label": label or euronext_ticker})
    save_config(config)
    print(f"{euronext_ticker} ({symbol}) a bien été ajouté.")
    return True


def remove(euronext_ticker: str) -> bool:
    """Retire un ticker (format EURONEXT) de tickers.json."""
    known = load_known_tickers()
    symbol = resolve_ticker(euronext_ticker, known)

    if symbol is None:
        print(f"Ticker non reconnu : {euronext_ticker}. Vérifiez {KNOWN_TICKERS_PATH.name}.")
        return False

    config = load_config()
    before = len(config["tickers"])
    config["tickers"] = [t for t in config["tickers"] if t["symbole"] != symbol]

    if len(config["tickers"]) == before:
        print(f"{euronext_ticker} ({symbol}) n'était pas dans la liste suivie.")
        return False

    save_config(config)
    print(f"{euronext_ticker} a bien été supprimé.")
    return True

def parse_ticker_arg(arg: str) -> tuple[str, str | None]:
    """
    Découpe un argument 'TICKER' ou 'TICKER:Label' en (ticker, label).
    Le label est None si non fourni.
    """
    if ":" in arg:
        ticker, label = arg.split(":", 1)
        label = label.strip() or None
        return ticker.strip(), label
    return arg.strip(), None

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
        print_help()
        sys.exit(0)

    raw_tickers = args[1:]
    if not raw_tickers:
        print("Aucun ticker fourni.")
        print_help(mode)
        sys.exit(1)

    if mode in ("-a", "--add"):
        for raw in raw_tickers:
            ticker, label = parse_ticker_arg(raw)
            add(ticker, label)
    elif mode in ("-r", "--remove"):
        for raw in raw_tickers:
            ticker, _ = parse_ticker_arg(raw)  # label ignoré pour remove
            remove(ticker)


if __name__ == "__main__":
    main()