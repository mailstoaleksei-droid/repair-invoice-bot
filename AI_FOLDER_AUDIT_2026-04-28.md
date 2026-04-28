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
- `Staack_Report`: separate active Staack downloader/report bot. Git repository exists, but remote points to old GitLab origin. Keep as separate project; update remote/checklist if it is still active.
- `Arbeitszeitplan der Fahrer - LKW`: LKW report bot copies exist in multiple places. Consolidate to one active folder and remove/archive duplicates.
- `Groo_automation`: active-looking automation with bot/service/logs and scheduled task. Add GitHub repo and checklist or archive if obsolete.
- `bonus_calculator`: has README-like documentation but no local Git repository. Add GitHub/checklist if active; do not store `venv` in repository.
- `GrooTarifrechner`: has documentation under scripts but no local Git repository. Add GitHub/checklist if active.
- `BONUS`, `Calc cost LKW`, `Fehrer_Container_LKW_Tag_Euro`, `Invoice`, `LKW rent price`, `YF_Report`: no confirmed Git/checklist from audit. Mark as unknown/legacy until owner confirms active use.

## Improvements

- Move inactive duplicates into `_archive` instead of keeping several runnable copies.
- Keep code and documentation in GitHub; keep secrets only in local `.env` or a proper secret manager.
- Keep source PDFs/reports in SharePoint/OneDrive for business access, but use GitHub only for code, docs, tests, and configuration templates.
- For long-term reliability, move scheduled jobs from a personal PC to a small server/cloud runner if the process becomes business-critical.
