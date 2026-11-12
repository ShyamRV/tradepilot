<#
.SYNOPSIS
  Postgres dump / restore drill for TradePilot.

.EXAMPLE
  .\scripts\backup_restore.ps1 backup
  .\scripts\backup_restore.ps1 restore -DumpFile .\backups\tradepilot.dump
  .\scripts\backup_restore.ps1 drill

Requires DATABASE_URL (postgresql://...) and PostgreSQL client tools on PATH.
Prefer an isolated restore target; never restore production dumps onto live
writers without an approved incident/cutover.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidateSet("backup", "restore", "drill")]
  [string]$Mode,

  [Parameter(Position = 1)]
  [string]$DumpFile,

  [string]$BackupDir = ".\backups"
)

$ErrorActionPreference = "Stop"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")

function Get-DatabaseUrl {
  if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL is required"
  }
  return $env:DATABASE_URL
}

function Assert-PgTools {
  foreach ($name in @("pg_dump")) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
      throw "Required tool not found on PATH: $name"
    }
  }
}

function Invoke-Backup {
  param([string]$OutFile)
  Assert-PgTools
  New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
  if (-not $OutFile) {
    $OutFile = Join-Path $BackupDir "tradepilot_$stamp.dump"
  }
  $url = Get-DatabaseUrl
  Write-Host "Backing up to $OutFile"
  & pg_dump --format=custom --no-owner --no-acl --dbname=$url --file=$OutFile
  if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
  Write-Host "Backup complete: $OutFile"
  Write-Host "Record backup_timestamp=$stamp for the restore drill."
  return $OutFile
}

function Invoke-Restore {
  param([string]$Path)
  if (-not $Path -or -not (Test-Path $Path)) {
    throw "Usage: backup_restore.ps1 restore -DumpFile <path>"
  }
  if ($env:ALLOW_DESTRUCTIVE_RESTORE -ne "yes") {
    throw "Refusing restore. Set ALLOW_DESTRUCTIVE_RESTORE=yes after confirming the target is isolated."
  }
  $url = Get-DatabaseUrl
  Write-Host "Restoring $Path into DATABASE_URL target"
  if (Get-Command pg_restore -ErrorAction SilentlyContinue) {
    & pg_restore --clean --if-exists --no-owner --no-acl --dbname=$url $Path
  } else {
    throw "pg_restore not found on PATH"
  }
  if ($LASTEXITCODE -ne 0) { throw "pg_restore failed with exit code $LASTEXITCODE" }
  Write-Host "Restore finished. Run migration/version, RLS, and smoke checks from docs/runbooks.md."
}

switch ($Mode) {
  "backup" {
    Invoke-Backup -OutFile $DumpFile | Out-Null
  }
  "restore" {
    Invoke-Restore -Path $DumpFile
  }
  "drill" {
    Write-Host "=== Backup/restore drill start ($stamp) ==="
    $dump = Invoke-Backup -OutFile (Join-Path $BackupDir "tradepilot_drill_$stamp.dump")
    Write-Host "Drill backup written. To complete the drill:"
    Write-Host "  1. Point DATABASE_URL at an isolated empty database."
    Write-Host "  2. `$env:ALLOW_DESTRUCTIVE_RESTORE='yes'; .\scripts\backup_restore.ps1 restore -DumpFile $dump"
    Write-Host "  3. Verify checksums, migration version, RLS, sampled tenant isolation."
    Write-Host "  4. Record RPO/RTO evidence in the incident/acceptance log."
    Write-Host "=== Drill backup phase complete ==="
  }
}
