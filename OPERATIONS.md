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

## Weekly automatic run

- Scheduled task name: `Repair Eingang Bot Weekly Invoice Processing`
- Schedule: every Monday at `09:00`
- Script: `weekly_process_invoices.ps1`
- The script checks only the root of `EingangsRG`; files in `manual` are excluded from the automatic batch.
- If PDF files are found, it runs `process_pdf_v7_3.py` with `OPENAI_ENABLED=true`, `TELEGRAM_ENABLED=true`, and `PROCESSING_MODE=report_only`.
- The final processing report is sent by the current processor to `PDF Processor Bot` when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured in `.env`.
- Install or refresh the Windows task with `install_weekly_task.cmd`; it calls `install_weekly_task.ps1` to avoid path quoting issues.
