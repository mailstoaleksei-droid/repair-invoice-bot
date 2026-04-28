# Changelog

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
