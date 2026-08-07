"""
Widget terminal affichant le prix de produits boursiers en temps réel.
Config via tickers.json (liste de tickers + fréquence de refresh).
"""

import json
import sys
import time
from pathlib import Path

import yfinance as yf
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

CONFIG_PATH = Path(__file__).parent / "tickers.json"

console = Console()


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

    if not config.get("tickers"):
        console.print("[red]Erreur : aucune entrée dans 'tickers'.[/red]")
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


def build_table(config: dict) -> Table:
    """Construit le tableau rich pour un cycle de refresh."""
    table = Table(title="Suivi boursier", show_lines=False)
    table.add_column("Actif", style="bold")
    table.add_column("Ticker", style="dim")
    table.add_column("Prix", justify="right")
    table.add_column("Variation", justify="right")

    for entry in config["tickers"]:
        symbol = entry["symbole"]
        label = entry.get("label", symbol)
        result = fetch_price(symbol)

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

        table.add_row(label, symbol, f"{price_str}€", change_str)

    return table


def main():
    config = load_config()
    refresh_seconds = config.get("refresh_seconds", 30)

    console.print(
        f"[dim]Rafraîchissement toutes les {refresh_seconds}s — Ctrl+C pour quitter[/dim]\n"
    )

    try:
        with Live(build_table(config), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(refresh_seconds)
                live.update(build_table(config))
    except KeyboardInterrupt:
        console.print("\n[dim]Widget arrêté.[/dim]")


if __name__ == "__main__":
    main()