#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# Se placer dans le dossier du script, peu importe d'où il est appelé
Set-Location -Path $PSScriptRoot

# Vérifie qu'au moins un moyen d'exécuter le script Python est disponible
$hasUv = [bool](Get-Command uv -ErrorAction SilentlyContinue)
$hasPython = [bool](Get-Command python -ErrorAction SilentlyContinue)

if (-not $hasUv -and -not $hasPython) {
    Write-Error "Ni 'uv' ni 'python' trouvés dans le PATH. Installe uv (https://docs.astral.sh/uv/) ou Python."
    exit 1
}

# Détermine le script à lancer : "run" lance le widget live (main.py),
# tout le reste est délégué au CLI de gestion des tickers (cli.py)
if ($args.Count -gt 0 -and $args[0] -eq "run") {
    $target = "main.py"
    $scriptArgs = $args[1..($args.Count - 1)]
    Clear-Host
} else {
    $target = "cli.py"
    $scriptArgs = $args
}

if ($hasUv) {
    uv run $target @scriptArgs
} else {
    $venvActivate = ".\.venv\Scripts\Activate.ps1"
    if (-not (Test-Path $venvActivate)) {
        Write-Error ".venv introuvable et 'uv' non disponible. Crée le venv : python -m venv .venv puis .\.venv\Scripts\pip install -r requirements.txt"
        exit 1
    }
    & $venvActivate
    python $target @scriptArgs
}