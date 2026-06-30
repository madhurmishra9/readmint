<#
  Readmint one-click deploy (Windows, PowerShell).

    .\deploy.ps1             # build + run on http://localhost:8080 (stub LLM)
    .\deploy.ps1 -Port 9000  # use a different host port

  A root .env file (if present) is passed into the container, so you can drop
  RF_LLM_* there to point at a live Cortex endpoint instead of the stub.

  If you get "running scripts is disabled", launch once with:
    powershell -ExecutionPolicy Bypass -File .\deploy.ps1
#>
[CmdletBinding()]
param(
  [int]$Port = 8080
)
$ErrorActionPreference = "Stop"
$Image = "readmint:local"
$Name  = "readmint"
Set-Location -Path $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "X Docker is not installed. Get it at https://docs.docker.com/get-docker/" -ForegroundColor Red
  exit 1
}
try { docker info | Out-Null } catch {
  Write-Host "X Docker is installed but the daemon isn't running. Start Docker Desktop and retry." -ForegroundColor Red
  exit 1
}

Write-Host "-> Building $Image ..." -ForegroundColor Cyan
docker build -t $Image .
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

Write-Host "-> Replacing any existing container ..." -ForegroundColor Cyan
docker rm -f $Name 2>$null | Out-Null

$envArgs = @()
if (Test-Path .env) { $envArgs = @("--env-file", ".env"); Write-Host "-> Using .env for configuration" -ForegroundColor Cyan }

Write-Host "-> Starting container on port $Port ..." -ForegroundColor Cyan
docker run -d --name $Name -p "${Port}:8080" @envArgs $Image | Out-Null
if ($LASTEXITCODE -ne 0) { throw "docker run failed" }

$url = "http://localhost:$Port"
Write-Host -NoNewline "-> Waiting for health"
foreach ($i in 1..30) {
  try {
    Invoke-RestMethod -Uri "$url/healthz" -TimeoutSec 2 | Out-Null
    Write-Host " - ready."
    Write-Host "OK Readmint is live at $url (API docs at $url/docs)" -ForegroundColor Green
    Start-Process $url
    exit 0
  } catch {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
  }
}

Write-Host ""
Write-Host "X Container started but never became healthy. Logs:" -ForegroundColor Red
docker logs $Name
exit 1
