# Stocks Widget

Petit widget terminal affichant en temps réel le prix d'une liste de produits boursiers (actions, ETF, indices) via [yfinance](https://github.com/ranaroussi/yfinance).

![status](https://img.shields.io/badge/status-perso-lightgrey)

## Aperçu

Un tableau qui se rafraîchit automatiquement dans le terminal, avec prix et variation journalière colorée (vert/rouge).

## Prérequis

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommandé) — ou `pip`/`venv` en fallback

## Installation

```bash
git clone <url-du-repo> ~/.widget/stocks
cd ~/.widget/stocks
uv sync
```

Sans `uv` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Éditer `tickers.json` :

```json
{
  "refresh_seconds": 30,
  "tickers": [
    { "symbol": "AAPL", "label": "Apple" },
    { "symbol": "CW8.PA", "label": "Amundi MSCI World" },
    { "symbol": "^GSPC", "label": "S&P 500" }
  ]
}
```

- `symbol` : ticker au format Yahoo Finance (`.PA` pour Paris, `.L` pour Londres, `^` pour un indice, pas de suffixe pour NASDAQ/NYSE).
- `label` : nom affiché dans le tableau (libre).
- `refresh_seconds` : fréquence de rafraîchissement. Éviter de descendre sous 15-30s pour ne pas se faire limiter par Yahoo Finance (API non officielle).

## Lancement

```bash
chmod +x run.sh
./run.sh
```

### Alias pratique (zsh)

Ajouter dans `~/.zshrc` :

```zsh
alias stocks="~/.widget/stocks/run.sh"
```

Puis `stocks` depuis n'importe où lance le widget.

## Structure

|--main.py
|--run.sh
|--README.md
|--tickers.json

## Notes

- yfinance est une API non officielle basée sur du scraping — pas de garantie de disponibilité à 100%, et un rafraîchissement trop fréquent peut entraîner un blocage temporaire de l'IP.
- Les erreurs sur un ticker (symbole invalide, données indisponibles) s'affichent en rouge dans le tableau sans interrompre le widget.

## Licence

Usage personnel.