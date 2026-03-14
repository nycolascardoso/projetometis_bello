# Runs the IPTU extraction
$ErrorActionPreference='Stop'
Set-Location ..\
. .\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING='utf-8'
python -m extracao_iptu.main
