# Local Python environment policy

Before running or debugging this project on a user's computer:

1. Run the read-only preflight first:
   `powershell -ExecutionPolicy Bypass -File scripts/preflight-local.ps1`.
2. Prefer the reproducible Conda environment from `environment.yml` and the
   Jupyter kernel `amazon-listing-auditor-py311`.
3. Never assume that `python`, `conda`, or `jupyter` is on `PATH`. Detect the
   executable and report its resolved path and version.
4. If Python 3.11, Conda, the environment, or required packages are missing,
   stop and explain what is missing. Provide the official Python/Anaconda
   download option, then ask the user for explicit permission before
   downloading, installing, creating, repairing, or changing any local
   environment.
5. A user's approval to run an audit is not approval to install software or
   alter an environment. Environment changes require a separate, explicit
   approval.
6. GitHub-hosted runners are ephemeral: the Actions workflow may install its
   declared Python version and dependencies without changing the user's local
   machine.
