# Quick diagnostics for non-technical users
$ErrorActionPreference='SilentlyContinue'
Set-Location ..\
$ok=@{}
$ok.Python = (python -V) -ne $null
$ok.Edge = (Get-Command msedge -ErrorAction SilentlyContinue) -ne $null
$ok.Tesseract = Test-Path 'C:\Program Files\Tesseract-OCR\tesseract.exe'
$planPath = (Select-String -Path extracao_imoveis\config.py -Pattern "PLANILHA_PATH\s*=\s*'(.*)'" | % { $_.Matches[0].Groups[1].Value })
$ok.Excel = Test-Path $planPath
try { $resp = Invoke-WebRequest -Uri 'https://tmi-apps.e-publica.net/cacador_eiptu/' -UseBasicParsing -TimeoutSec 15; $ok.UrlReach = $resp.StatusCode -eq 200 } catch { $ok.UrlReach = $false }
$ok | Format-List
