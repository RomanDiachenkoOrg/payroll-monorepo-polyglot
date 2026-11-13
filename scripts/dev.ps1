<#
.SYNOPSIS
  Developer helper for Windows (equivalent of the Makefile targets).

.EXAMPLE
  ./scripts/dev.ps1 up
  ./scripts/dev.ps1 test
  ./scripts/dev.ps1 reset
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "reset", "logs", "ps", "test", "test-api", "test-reports", "test-notifier", "test-web")]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

function Invoke-In([string]$dir, [scriptblock]$block) {
    Push-Location (Join-Path $root $dir)
    try { & $block; if ($LASTEXITCODE) { throw "Command failed in $dir" } } finally { Pop-Location }
}

function Test-Reports {
    if (Get-Command go -ErrorAction SilentlyContinue) {
        Invoke-In "services/reports" { go test ./... }
    } else {
        Write-Host "Go not found, running reports tests in Docker"
        docker run --rm -v "${root}/services/reports:/src" -w /src golang:1.22 go test ./...
    }
}

try {
    switch ($Command) {
        "up" {
            docker compose up --build -d
            Write-Host "Web: http://localhost:8080  API docs: http://localhost:8000/api/docs"
        }
        "down" { docker compose down }
        "reset" { docker compose down -v; docker compose up --build -d }
        "logs" { docker compose logs -f --tail=100 }
        "ps" { docker compose ps }
        "test-api" { Invoke-In "services/api" { python -m pytest } }
        "test-reports" { Test-Reports }
        "test-notifier" { Invoke-In "services/notifier" { npm test } }
        "test-web" { Invoke-In "web" { npm test } }
        "test" {
            Invoke-In "services/api" { python -m pytest }
            Test-Reports
            Invoke-In "services/notifier" { npm test }
            Invoke-In "web" { npm test }
        }
    }
} finally {
    Pop-Location
}
