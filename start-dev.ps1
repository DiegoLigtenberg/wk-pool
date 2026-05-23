# Start WK Pool backend + frontend in this terminal.
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
Require-Command "npx"

if (-not (Test-Path $BackendDir)) {
    throw "Backend folder not found: $BackendDir"
}
if (-not (Test-Path $FrontendDir)) {
    throw "Frontend folder not found: $FrontendDir"
}

Write-Host ""
Write-Host "WK Pool dev servers:"
Write-Host "  Backend:  http://127.0.0.1:8000"
Write-Host "  Frontend: http://127.0.0.1:5173"
Write-Host "  Press Ctrl+C to stop both."
Write-Host ""

Set-Location $Root

$backendCmd = "cd /d `"$BackendDir`" && poetry run wk-pool-backend"
$frontendCmd = "cd /d `"$FrontendDir`" && npm run dev"

& npx --yes concurrently `
    --names "backend,frontend" `
    --prefix-colors "cyan,magenta" `
    --kill-others `
    $backendCmd `
    $frontendCmd
