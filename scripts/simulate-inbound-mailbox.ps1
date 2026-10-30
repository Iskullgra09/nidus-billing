param(
  [Parameter(Mandatory = $true)]
  [string]$To
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python scripts/simulate_inbound_mailbox.py --to $To
exit $LASTEXITCODE
