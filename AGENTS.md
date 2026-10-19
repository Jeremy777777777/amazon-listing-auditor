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

# Copy-ready audit workflow

For paste-ready listing corrections, follow `references/listing-copy-style.md`.
Read actual RAM/storage choices from the listing's Customize controls using an
authorized browser/provider, preserving ASIN, timestamp and units. Pass the
structured capture with `--customization-evidence`; title text, platform maxima
and unitless summary tables are not substitutes. Keep original/factory facts,
page attributes, purchasable options and selected values separate. Do not infer
a default or factory configuration from an unselected/first option.

Finished title, five bullets and HTML description must not contain VERIFY/TODO
placeholders or editorial instructions. Put unknown optional facts and missing
sources in audit notes; withhold copy if core identity/warranty is unmapped.
Export complete strings into the first sheet `可复制文案`, column B, and the
matching template recommendation cells. Never split the copyable value into
continuation rows. Preserve original captured content separately. Rebuild the
requested product's example after changing copy generation, verify no unresolved
markers or wrong option units remain, then deliver the reviewed workbook and
upload the authorized workflow changes.
