# Stocks Widget

Widget terminal affichant en temps réel le prix d'une liste de produits boursiers (actions, ETF, indices) via [yfinance](https://github.com/ranaroussi/yfinance).

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

Pour éditer la table deux options:
1. Éditer `tickers.json` :

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

2. Utiliser une commande:
```bash
./run.sh -a|--add [TICKERS]:[LABEL] 
```
La commande est plus robuste car elle gère directement la conversion EURONEXT -> yfinance des tickers.  
Attention: si une action / ETF / indice n'est pas pas reconnu veuillez vérifier son existence dans le fichier `actions_connues.json`.  
Pour retirer une action il suffit d'utilier `-r|--remove`
````bash
./run.sh -r|--remove [TICKER]
````

Vous pouvez par ailleurs modifier le label via la commande `-m|--modify`
````bash
./run.sh -m|--modify [TICKER]:[NOUVEAU LABEL]
````
## Lancement

```bash
chmod +x run.sh
./run.sh run
```

Toute commande dont le premier argument est `run` lance le widget live
(`main.py`). Sans `run` en premier argument (y compris `./run.sh` seul),
la commande est déléguée au CLI de gestion des tickers (`cli.py`, voir
plus bas).

### Tri de l'affichage

```bash
./run.sh run --sort -c|-d|-vc|-vd|-ac|-ad
```

- `-c` : prix croissant
- `-d` : prix décroissant (défaut si `--sort` est utilisé sans ordre)
- `-vc` : variation croissante
- `-vd` : variation décroissante
- `-ac` : alphabétique A → Z (label)
- `-ad` : alphabétique Z → A (label)

Sans `--sort`, l'ordre est celui de `tickers.json`. Les tickers en
erreur (données indisponibles) restent toujours en bas du tableau,
quel que soit le tri.


**Pour toute aide veuillez utiliser la fonction d'aide du cli:**
````bash
./run.sh (commande) -h|--help
````
### Alias pratique (zsh)

Ajouter dans `~/.zshrc` :

```zsh
alias stocks="~/.widget/stocks/run.sh"
```

Puis `stocks run` depuis n'importe où lance le widget.

## Structure

|--main.py  
|--cli.py  
|--run.sh  
|--run.ps1  
|--README.md  
|--tickers.json  
|--cache.json  
|--actions_connues.json  

## Notes

- yfinance est une API non officielle basée sur du scraping — pas de garantie de disponibilité à 100%, et un rafraîchissement trop fréquent peut entraîner un blocage temporaire de l'IP.
- Les erreurs sur un ticker (symbole invalide, données indisponibles) s'affichent en rouge dans le tableau sans interrompre le widget.
- Un avertissement apparaît au-dessus du tableau dans les 15 minutes précédant la clôture d'Euronext Paris (17:30, heure de Paris, CET/CEST géré automatiquement) ou si le marché est fermé (>=17h30 et <=9h ou weekend), si au moins un ticker suivi a le suffixe `.PA`. Les autres places boursières ne sont pas gérées pour l'instant.
Attention ne gère pas les autres dates de fermeture de bourse.

## Licence

Usage personnel.
