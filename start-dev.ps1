# Start WK Pool backend + frontend for local development.
# Usage (from repo root):  .\start-dev.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "src\backend"
$FrontendDir = Join-Path $Root "src\frontend"

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing '$Name' on PATH. Install it and try again."
    }
}

Require-Command "poetry"
Require-Command "npm"

if (-not (Test-Path $BackendDir)) {
    throw "Backend folder not found: $BackendDir"
}
if (-not (Test-Path $FrontendDir)) {
    throw "Frontend folder not found: $FrontendDir"
}

$backendCmd = "Set-Location -LiteralPath '$BackendDir'; poetry run wk-pool-backend"
$frontendCmd = "Set-Location -LiteralPath '$FrontendDir'; npm run dev"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd) | Out-Null
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $frontendCmd) | Out-Null

Write-Host ""
Write-Host "WK Pool dev servers starting in two windows:"
Write-Host "  Backend:  http://127.0.0.1:8000"
Write-Host "  Frontend: http://127.0.0.1:5173"
Write-Host ""
Write-Host "Close each window (or Ctrl+C in it) to stop that service."
