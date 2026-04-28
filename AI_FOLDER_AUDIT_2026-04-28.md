# AI Folder Audit - 2026-04-28

Root: `C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Groo Forest GmbH\AI`

## Overall

- Active invoice project: `Repair Eingang Bot`.
- Main duplicate risk: `pdf_processor_project` and `repair-invoice-bot` overlap with the invoice project.
- Several folders have no local `.git` repository and no project checklist; they should be archived or normalized.
- Recommended standard for every active project: `README.md`, project checklist, `.env.example`, `.gitignore`, GitHub remote, run script, operations notes.

## Projects

- `Repair Eingang Bot`: active invoice/PDF project. GitHub: yes, `mailstoaleksei-droid/repair-invoice-bot`. Checklist: yes. Keep.
- `repair-invoice-bot`: duplicate/older clone of the same invoice project and same GitHub remote. Archive or delete after confirming no unique files are needed.
- `pdf_processor_project`: old invoice/PDF processor copy with legacy Telegram and processor files. Archive or delete after final comparison with `Repair Eingang Bot`.
- `Staack_Report`: separate Staack downloader/report bot. Git repository exists; `PROJECT_CHECKLIST.md` added and GitHub remote `github` prepared as `mailstoaleksei-droid/staack-report`. Current Windows task `StaackBot` points to `Groo Forest GmbH\Bot`, not this AI folder, so production folder needs confirmation.
- `Arbeitszeitplan der Fahrer - LKW`: LKW report bot copies exist in multiple places. Active Windows tasks point to `C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Fahrer\Arbeitszeitplan der Fahrer - LKW\lkw_report_bot`; AI copy should be treated as duplicate/archive unless proven otherwise.
- `Groo_automation`: local Git repository initialized, `PROJECT_CHECKLIST.md` and `README.md` added, `origin` prepared as `mailstoaleksei-droid/groo-automation`. Current task `Groo Monthly Report` points to this folder but references `run_monthly_report.bat`; confirm/fix missing entry point.
- `bonus_calculator`: local Git repository initialized, `PROJECT_CHECKLIST.md` added, `origin` prepared as `mailstoaleksei-droid/bonus-calculator`. `venv`, logs, backups, generated outputs, and Excel workbooks are excluded.
- `GrooTarifrechner`: local Git repository initialized, `PROJECT_CHECKLIST.md` and `README.md` added, `origin` prepared as `mailstoaleksei-droid/groo-tarifrechner`. Production HTML version still needs confirmation.
- `BONUS`, `Calc cost LKW`, `Fehrer_Container_LKW_Tag_Euro`, `Invoice`, `LKW rent price`, `YF_Report`: no confirmed Git/checklist from audit. Mark as unknown/legacy until owner confirms active use.

## Improvements

- Move inactive duplicates into `_archive` instead of keeping several runnable copies.
- Keep code and documentation in GitHub; keep secrets only in local `.env` or a proper secret manager.
- Keep source PDFs/reports in SharePoint/OneDrive for business access, but use GitHub only for code, docs, tests, and configuration templates.
- For long-term reliability, move scheduled jobs from a personal PC to a small server/cloud runner if the process becomes business-critical.

## GitHub Status

- GitHub repositories still need to be created before push:
- `mailstoaleksei-droid/staack-report`
- `mailstoaleksei-droid/groo-automation`
- `mailstoaleksei-droid/bonus-calculator`
- `mailstoaleksei-droid/groo-tarifrechner`
