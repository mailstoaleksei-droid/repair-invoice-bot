# Changelog

## 2026-04-28

- Added dynamic path configuration so the project can run from `AI\Repair Eingang Bot` while still processing files in `Eingangs Rechnungen\EingangsRG`.
- Fixed `AI Assisted` reporting to count unique invoices/files instead of repeated fallback attempts.
- Added `Review Queue` sheet to each processing report with partial, failed, duplicate, and other problematic invoices for manual follow-up.
- Increased Telegram bot timeout support for longer AI-enabled runs.
- Added a project sync helper for checklist logging and GitHub publishing.
