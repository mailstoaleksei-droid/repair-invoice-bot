# AI Folder Audit - 2026-04-28

Root: `C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Groo Forest GmbH\AI`

## Overall

- Active invoice project: `Repair Eingang Bot`.
- Duplicate cleanup completed: `pdf_processor_project` and `repair-invoice-bot` were removed from the AI root after saving a local cleanup archive.
- Several folders have no local `.git` repository and no project checklist; they should be archived or normalized.
- Recommended standard for every active project: `README.md`, project checklist, `.env.example`, `.gitignore`, GitHub remote, run script, operations notes.

## Projects

- `Repair Eingang Bot`: active invoice/PDF project. GitHub: yes, `mailstoaleksei-droid/repair-invoice-bot`. Checklist: yes. Keep.
- `repair-invoice-bot`: removed from AI root. Uncommitted status, patch, selected untracked files, and manifest were saved in `AI\_archive\duplicate_cleanup_20260428_154926`.
- `pdf_processor_project`: removed from AI root. Markdown docs and manifest were saved in `AI\_archive\duplicate_cleanup_20260428_154926`.
- `Staack_Report`: separate Staack downloader/report bot. GitHub repo created and pushed: `mailstoaleksei-droid/staack-report`. Current Windows task `StaackBot` points to `Groo Forest GmbH\Bot`, not this AI folder, so production folder needs confirmation. Local working tree still contains pre-existing uncommitted Staack changes.
- `Arbeitszeitplan der Fahrer - LKW`: LKW report bot copies exist in multiple places. Active Windows tasks point to `C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Fahrer\Arbeitszeitplan der Fahrer - LKW\lkw_report_bot`; AI copy should be treated as duplicate/archive unless proven otherwise.
- `Groo_automation`: GitHub repo created and pushed: `mailstoaleksei-droid/groo-automation`. Missing scheduled entry point `run_monthly_report.bat` was restored; end-to-end live test still needed.
- `bonus_calculator`: GitHub repo created and pushed: `mailstoaleksei-droid/bonus-calculator`. `venv`, logs, backups, generated outputs, and Excel workbooks are excluded.
- `GrooTarifrechner`: GitHub repo created and pushed: `mailstoaleksei-droid/groo-tarifrechner`. Production HTML version still needs confirmation.
- `BONUS`, `Calc cost LKW`, `Fehrer_Container_LKW_Tag_Euro`, `Invoice`, `LKW rent price`, `YF_Report`: no confirmed Git/checklist from audit. Mark as unknown/legacy until owner confirms active use.

## Improvements

- Move inactive duplicates into `_archive` instead of keeping several runnable copies.
- Keep code and documentation in GitHub; keep secrets only in local `.env` or a proper secret manager.
- Keep source PDFs/reports in SharePoint/OneDrive for business access, but use GitHub only for code, docs, tests, and configuration templates.
- For long-term reliability, move scheduled jobs from a personal PC to a small server/cloud runner if the process becomes business-critical.

## GitHub Status

- GitHub repositories created and initial `main` branch pushed:
- `mailstoaleksei-droid/staack-report`
- `mailstoaleksei-droid/groo-automation`
- `mailstoaleksei-droid/bonus-calculator`
- `mailstoaleksei-droid/groo-tarifrechner`

Helper files in AI root:
- `GITHUB_REPOS_TO_CREATE_2026-04-28.md`
- `PUSH_PROJECT_REPOS_AFTER_GITHUB_CREATE.ps1`
- `CLOUD_RUNNER_PLAN_2026-04-28.md`
