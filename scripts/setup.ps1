# One-time setup: creates venv and installs requirements
$ErrorActionPreference='Stop'
Set-Location ..\
if (!(Test-Path .venv)) { Write-Host 'Creating venv...'; py -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
if (Test-Path requirements.lock.txt) { pip install -r requirements.lock.txt } else { pip install -r requirements.txt }
Write-Host 'Setup complete.'
