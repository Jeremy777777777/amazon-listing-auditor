# Local Python and Jupyter workflow

The reproducible local target is **Python 3.11** in a dedicated Conda
environment. Do not use or modify the Anaconda `base` environment for this
project.

## 1. Read-only preflight

Run this before every local audit or debugging session:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight-local.ps1
```

If Conda is installed outside a standard path:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight-local.ps1 `
  -CondaExe "E:\Coding\Scripts\conda.exe" `
  -EnvironmentPath "E:\Coding\envs\amazon-listing-auditor-py311"
```

The preflight is read-only. It prints the resolved executable, environment
path, Python version, and dependency status.

## 2. Missing environment policy

If Python, Conda, the environment, or a dependency is missing:

1. Stop the audit.
2. State exactly what is missing and provide the official download page.
3. Ask the user for explicit permission to install, create, update, or repair
   the environment.
4. Only after permission, run the relevant setup command.

An audit request alone does not authorize local software installation.

## 3. Create or reproduce the environment

After permission:

```powershell
& "<path-to-conda>\Scripts\conda.exe" env create `
  --prefix "<path-to-conda>\envs\amazon-listing-auditor-py311" `
  --file environment.yml
```

For an existing environment:

```powershell
& "<path-to-conda>\Scripts\conda.exe" env update `
  --prefix "<path-to-conda>\envs\amazon-listing-auditor-py311" `
  --file environment.yml `
  --prune
```

Register the Jupyter kernel:

```powershell
& "<path-to-conda>\envs\amazon-listing-auditor-py311\python.exe" -m ipykernel install `
  --user `
  --name amazon-listing-auditor-py311 `
  --display-name "Python 3.11 (Amazon Listing Auditor)"
```

In Jupyter Notebook/Lab, select **Python 3.11 (Amazon Listing Auditor)**.

## 4. Validate and test

```powershell
& "<path-to-conda>\envs\amazon-listing-auditor-py311\python.exe" scripts/check_python.py `
  --strict-target `
  --check-dependencies

& "<path-to-conda>\envs\amazon-listing-auditor-py311\python.exe" -m pytest
```

GitHub Actions uses its own temporary Python environment. It does not use or
change the user's local Conda installation.
