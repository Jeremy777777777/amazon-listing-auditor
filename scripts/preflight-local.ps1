[CmdletBinding()]
param(
    [string]$CondaExe,
    [string]$EnvironmentPath
)

$ErrorActionPreference = 'Stop'
$targetPython = '3.11'
$environmentName = 'amazon-listing-auditor-py311'

function Resolve-CondaExecutable {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (Test-Path -LiteralPath $ExplicitPath) {
            return (Resolve-Path -LiteralPath $ExplicitPath).Path
        }
        throw "The supplied Conda executable does not exist: $ExplicitPath"
    }

    $command = Get-Command conda -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidateRoots = @(
        (Join-Path $env:USERPROFILE 'anaconda3'),
        (Join-Path $env:USERPROFILE 'miniconda3'),
        (Join-Path $env:LOCALAPPDATA 'anaconda3'),
        'C:\ProgramData\anaconda3',
        'C:\ProgramData\miniconda3'
    )
    foreach ($root in $candidateRoots) {
        $candidate = Join-Path $root 'Scripts\conda.exe'
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

$conda = Resolve-CondaExecutable -ExplicitPath $CondaExe
if (-not $conda) {
    Write-Error @"
Conda was not found. Python $targetPython in an isolated Conda environment is required for the reproducible local workflow.
Download Anaconda or Miniconda from https://www.anaconda.com/download or https://docs.conda.io/projects/miniconda/.
Do not install or change the user's environment automatically. Ask the user for explicit permission to help install or debug it.
"@
    exit 10
}

if (-not $EnvironmentPath) {
    $condaRoot = Split-Path -Parent (Split-Path -Parent $conda)
    $EnvironmentPath = Join-Path $condaRoot "envs\$environmentName"
}

$python = Join-Path $EnvironmentPath 'python.exe'
Write-Host "Conda executable: $conda"
Write-Host "Expected environment: $EnvironmentPath"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error @"
The $environmentName environment is missing.
After receiving explicit user permission, create it from environment.yml with:
  & '$conda' env create --prefix '$EnvironmentPath' --file environment.yml
"@
    exit 11
}

& $python scripts/check_python.py --strict-target --check-dependencies
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
The environment exists but is not ready. Ask the user for explicit permission before installing packages or repairing it.
With permission, update it with:
  & '$conda' env update --prefix '$EnvironmentPath' --file environment.yml --prune
"@
    exit 12
}

Write-Host 'Local environment preflight: PASS'
Write-Host "Jupyter kernel: Python 3.11 (Amazon Listing Auditor)"
