# Changelog

## 2026-04-30

- Added Scania Finance `SRD...` invoice support, including `Kennzeichen: KO-HH 322` truck normalization and `Netto gesamt (EUR)` total extraction.
- Added `KO-HH` truck-number normalization to the shared truck reference module.
- Verified Scania regressions for `SCHWM02656`, `SCHWM03267`, and `SCHWM03372`: invoice dates now come from `RE-DATUM`, and Scania `AUFTRAGS-NR.` values are not used as invoice numbers.
- Added a dedicated `Problem Invoices` sheet to processing reports with invoice number, source file, status, reason, missing fields, supplier, date, truck, total, and AI notes.
- Added problematic invoice details to the Telegram final summary so failed and partial invoices are visible without opening the Excel file.
- Fixed Scania classification when OCR contains `#splminfo` and `SCH...` invoice numbers but not the word `SCANIA` near the top of the document.
- Fixed Scania invoice extraction to prefer `RE-NR.` / `SCH...` invoice numbers and avoid using `AUFTRAGS-NR.` values such as `47321-1-1-01`.
- Fixed Scania truck extraction for `AMTL.KENNZ: GR-OO 1511` and maintenance-contract `Kennzeichen: GR-OO 2456` style lines.
- Added multi-truck Scania Wartungsvertrag parsing so one invoice can produce one Excel row per truck with the matching per-truck amount.
- Fixed Scania invoice-date priority to avoid taking vehicle header dates instead of `RE-DATUM`.

## 2026-04-28

- Added dynamic path configuration so the project can run from `AI\Repair Eingang Bot` while still processing files in `Eingangs Rechnungen\EingangsRG`.
- Fixed `AI Assisted` reporting to count unique invoices/files instead of repeated fallback attempts.
- Added `Review Queue` sheet to each processing report with partial, failed, duplicate, and other problematic invoices for manual follow-up.
- Increased Telegram bot timeout support for longer AI-enabled runs.
- Added a project sync helper for checklist logging and GitHub publishing.
- Added weekly Monday 09:00 automation script and Scheduled Task installer for AI-enabled processing of `EingangsRG`.
- Documented the 95%+ automation target, bot ownership, and manual-error feedback flow.
- Fixed Scheduled Task installation to handle project paths with spaces.
- Added AI folder audit covering duplicate projects, checklist/GitHub status, and storage recommendations.
- Updated AI folder audit after preparing local Git/checklists for Staack, Groo Automation, Bonus Calculator, and Groo Tarifrechner.
- Documented Groo Automation scheduled launcher restoration in the AI folder audit.
- Deleted duplicate invoice project folders after saving a local cleanup archive and added AI-root follow-up documents for GitHub repo creation and Cloud Runner planning.
- Marked Staack, Groo Automation, Bonus Calculator, and Groo Tarifrechner GitHub repositories as created and pushed.
- Recorded Staack active-code push and the remaining manual Scheduled Task switch requirement.
- Archived legacy `Groo Forest GmbH\Bot` contents and neutralized the old Staack scheduled-task entry point with a no-op stub.
- Recorded deletion of legacy Scheduled Task `\Staack\StaackBot`; Staack now runs manually via Telegram bot.
