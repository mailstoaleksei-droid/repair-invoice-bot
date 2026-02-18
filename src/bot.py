"""Repair Invoice Bot — Telegram entry point."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from src.config import TELEGRAM_BOT_TOKEN, WHITELIST_USER_IDS

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


# ── Access control ────────────────────────────────────────


def _allowed(user_id: int) -> bool:
    return not WHITELIST_USER_IDS or user_id in WHITELIST_USER_IDS


# ── /start ────────────────────────────────────────────────


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id):
        await update.message.reply_text("Zugriff verweigert.")
        return

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📄 Обработать счета", callback_data="scan")],
            [InlineKeyboardButton("📁 Manual", callback_data="manual")],
        ]
    )
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}!\n"
        "Repair Invoice Bot готов к работе.",
        reply_markup=keyboard,
    )


# ── /health ───────────────────────────────────────────────


async def cmd_health(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id):
        return
    # TODO: ping DB + OpenAI
    await update.message.reply_text("✅ Bot is running.")


# ── /cost ─────────────────────────────────────────────────


async def cmd_cost(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id):
        return
    # TODO: read today's cost from processing_log
    await update.message.reply_text("💰 Расходы: $0.00 / 0 счетов (сегодня)")


# ── Callback: scan folder ─────────────────────────────────


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not _allowed(query.from_user.id):
        await query.edit_message_text("Zugriff verweigert.")
        return

    if query.data == "scan":
        await _handle_scan(query, ctx)
    elif query.data == "confirm_process":
        await _handle_process(query, ctx)
    elif query.data == "manual":
        await _handle_manual(query, ctx)
    elif query.data == "cancel":
        await query.edit_message_text("Отменено.")


async def _handle_scan(query, ctx) -> None:
    from src.config import PDF_FOLDER

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    count = len(pdf_files)

    if count == 0:
        await query.edit_message_text("📁 Папка пуста — нет новых PDF.")
        return

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"✅ Обработать {count} шт.", callback_data="confirm_process")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
        ]
    )
    await query.edit_message_text(
        f"📄 Найдено **{count}** новых PDF в папке.\n\nОбработать?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def _handle_process(query, ctx) -> None:
    await query.edit_message_text("⏳ Запуск обработки...")
    # TODO: call pipeline orchestrator
    await query.edit_message_text("🚧 Pipeline ещё не реализован (Phase 1).")


async def _handle_manual(query, ctx) -> None:
    from src.config import MANUAL_FOLDER

    if not MANUAL_FOLDER.exists():
        await query.edit_message_text("📁 Папка manual/ пуста.")
        return

    files = list(MANUAL_FOLDER.glob("*.pdf"))
    if not files:
        await query.edit_message_text("📁 Папка manual/ пуста.")
        return

    text = f"📁 **Manual** — {len(files)} файл(ов):\n\n"
    for f in files[:20]:
        text += f"• `{f.name}`\n"
    if len(files) > 20:
        text += f"\n...и ещё {len(files) - 20}"

    await query.edit_message_text(text, parse_mode="Markdown")


# ── Main ──────────────────────────────────────────────────


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("cost", cmd_cost))
    app.add_handler(CallbackQueryHandler(on_callback))

    log.info("Repair Invoice Bot started (polling).")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
