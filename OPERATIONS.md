# Operations

## Run the processor

1. Put new PDF invoices into `EingangsRG`.
2. Start `start_bot.cmd` or run `python telegram_bot_v4_updated.py`.
3. In Telegram, use `PDF Processor Bot` and press `🔄 Обработать PDF`.
4. The bot launches `process_pdf_v7_3.py` with OpenAI fallback enabled if it is configured in `.env`.
5. Review the generated Excel report in `reports/`, especially the `Review Queue` sheet for invoices that need manual follow-up.

## Sync project changes

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync_project_state.ps1 -Message "Describe the update"
```

This stages changes, appends a timestamped sync line to the live checklist, commits, and pushes to `origin/main`.

## Current operating notes

- The incoming data source remains `Eingangs Rechnungen\EingangsRG`.
- The `manual` subfolder is not part of the normal incoming batch.
- AI should remain enabled for production-level automation targets.
