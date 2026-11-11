"""
Widget terminal affichant le prix de produits boursiers en temps réel.
Config via tickers.json (liste de tickers + fréquence de refresh).
"""

import json
import sys
import time
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

CONFIG_PATH = Path(__file__).parent / "tickers.json"
CACHE_PATH = Path(__file__).parent / "cache.json"

MAX_INTRADAY_POINTS = 200
MAX_WEEKLY_POINTS = 5
#TIME_BETWEEN_SAVE_S = 300
console = Console()

# Tri (./run.sh run --sort -c|-d|-vc|-vd|-ac|-ad)
# clé du résultat (ou "label"), reverse
SORT_OPTIONS = {
    "-c": ("price", False),
    "-d": ("price", True),
    "-vc": ("change_pct", False),
    "-vd": ("change_pct", True),
    "-ac": ("label", False),
    "-ad": ("label", True),
}
DEFAULT_SORT = SORT_OPTIONS["-d"]  # prix décroissant

# Avertissement de clôture (Euronext Paris uniquement, pour l'instant)
PARIS_TZ = ZoneInfo("Europe/Paris")
PARIS_MARKET_CLOSE = dt_time(17, 30)
CLOSE_WARNING_WINDOW_MIN = 15

def load_cache() -> dict:
    """Charge le cache d'historique, ou retourne une structure vide si absent."""
    if not CACHE_PATH.exists():
        return {}

    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Erreur : cache corrompu ({e}). Réinitialisation.[/red]")
        return {}

def load_config() -> dict:
    """Charge tickers.json. Quitte proprement si le fichier est absent/invalide."""
    if not CONFIG_PATH.exists():
        console.print(f"[red]Erreur : {CONFIG_PATH} introuvable.[/red]")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Erreur : tickers.json mal formé ({e}).[/red]")
        sys.exit(1)

    return config


def fetch_price(symbol: str) -> dict:
    """
    Récupère le dernier prix et la variation journalière pour un ticker.
    Retourne un dict avec un statut 'ok' ou 'error' pour ne jamais planter
    la boucle principale sur un ticker en échec.
    """
    try:
        ticker = yf.Ticker(symbol)
        # fast_info est plus léger que .info (moins de requêtes, plus rapide)
        info = ticker.fast_info

        price = info.get("lastPrice")
        prev_close = info.get("previousClose")

        if price is None or prev_close is None:
            return {"status": "error", "message": "Données indisponibles"}

        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        return {
            "status": "ok",
            "price": price,
            "change": change,
            "change_pct": change_pct,
        }

    except Exception as e:
        # yfinance peut lever plusieurs types d'exceptions (réseau, parsing, etc.)
        # On les attrape toutes pour ne jamais casser l'affichage global.
        return {"status": "error", "message": str(e)[:40]}

def get_total_portfolio_value(config: dict) -> float:

    return sum(
        ticker["pru"] * ticker["quantity"] if ticker.get("pru") and ticker.get("quantity") else 0
        for ticker in config["tickers"]
    )


def parse_sort_args(argv: list[str]) -> tuple[str, bool] | None:
    """
    Cherche --sort dans les arguments et retourne (clé, reverse), ou None si
    aucun tri n'est demandé. Clé du résultat de fetch_price ("price",
    "change_pct") ou "label". Si --sort est fourni sans ordre valide juste
    après, le tri par défaut (prix décroissant) est utilisé.
    """
    if "--sort" not in argv:
        return None

    idx = argv.index("--sort")
    order_flag = argv[idx + 1] if idx + 1 < len(argv) else None
    return SORT_OPTIONS.get(order_flag, DEFAULT_SORT)


def paris_market_closing_warning(config: dict) -> str | None:
    """
    Retourne un message d'avertissement si le marché de Paris approche de sa
    clôture (17:30 heure de Paris, gère automatiquement CET/CEST), et qu'au
    moins un ticker suivi est coté sur Euronext Paris (suffixe .PA). None
    sinon. Ne gère pas les jours fériés, ni les autres places boursières.
    """
    if not any(entry["symbole"].endswith(".PA") for entry in config["tickers"]):
        return None

    now = datetime.now(PARIS_TZ)
    if now.weekday() >= 5:  # samedi/dimanche : marché fermé
        return None

    close_dt = now.replace(
        hour=PARIS_MARKET_CLOSE.hour, minute=PARIS_MARKET_CLOSE.minute,
        second=0, microsecond=0,
    )
    window_start = close_dt - timedelta(minutes=CLOSE_WARNING_WINDOW_MIN)

    if window_start <= now <= close_dt:
        minutes_left = max(0, int((close_dt - now).total_seconds() // 60))
        return f"Clôture du marché de Paris dans {minutes_left} min (17:30, heure de Paris)."

    return "Marché fermé"


def build_table(config: dict, sort_spec: tuple[str, bool] | None = None) -> Table:
    """Construit le tableau rich pour un cycle de refresh."""

    table = Table(title="Suivi boursier", show_lines=False)
    table.add_column("Actif", style="bold")
    table.add_column("Ticker", style="dim")
    table.add_column("Prix", justify="right")
    table.add_column("PRU", justify="right")
    table.add_column("Variation", justify="right")

    rows = []
    for entry in config["tickers"]:
        symbol = entry["symbole"]
        label = entry.get("label", symbol)
        pru = entry.get("pru", "--")
        rows.append({"symbol": symbol, "label": label, "pru": pru, "result": fetch_price(symbol)})

    ok_rows = [r for r in rows if r["result"]["status"] == "ok"]
    error_rows = [r for r in rows if r["result"]["status"] != "ok"]

    if sort_spec:
        key, reverse = sort_spec
        if key == "label":
            ok_rows.sort(key=lambda r: r["label"].lower(), reverse=reverse)
        else:
            ok_rows.sort(key=lambda r: r["result"][key], reverse=reverse)

    for row in ok_rows + error_rows:
        symbol = row["symbol"]
        label = row["label"]
        pru = row["pru"]
        result = row["result"]

        if result["status"] == "error":
            table.add_row(label, symbol, "—", Text(result["message"], style="red"))
            continue

        price_str = f"{result['price']:.2f}"
        change = result["change"]
        change_pct = result["change_pct"]

        color = "green" if change >= 0 else "red"
        sign = "+" if change >= 0 else ""
        change_str = Text(
            f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)", style=color
        )

        table.add_row(label, symbol, f"{price_str}€", f"{pru} €", change_str)

    return table


def build_renderable(config: dict, sort_spec: tuple[str, bool] | None = None):
    """Assemble le tableau et l'avertissement de clôture (s'il y en a un) pour Live."""
    table = build_table(config, sort_spec)
    warning = paris_market_closing_warning(config)

    if warning:
        return Group(Text(f"⚠ {warning}", style="bold yellow"), table)
    return table


def main():
    config = load_config()
    refresh_seconds = config.get("refresh_seconds", 30)
    sort_spec = parse_sort_args(sys.argv[1:])

    console.print(
        f"[dim]Rafraîchissement toutes les {refresh_seconds}s — Ctrl+C pour quitter[/dim]\n"
    )

    try:
        with Live(build_renderable(config, sort_spec), refresh_per_second=1, console=console) as live:
            while True:
                console.print(f"Valeur totale intestie: {get_total_portfolio_value(config)} €")
                time.sleep(refresh_seconds)
                live.update(build_renderable(config, sort_spec))
    except KeyboardInterrupt:
        console.print("\n[dim]Widget arrêté.[/dim]")


if __name__ == "__main__":
    main()