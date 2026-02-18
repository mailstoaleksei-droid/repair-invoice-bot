"""Repair Invoice Bot — Telegram entry point."""

import asyncio
import logging
import threading

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

# Lock to prevent concurrent processing
_processing_lock = threading.Lock()


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
    lines = ["✅ Bot is running."]

    # Check DB
    try:
        from src.modules.db import get_connection
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        lines.append("✅ PostgreSQL connected.")
    except Exception as e:
        lines.append(f"❌ PostgreSQL: {e}")

    # Check OpenAI
    try:
        from openai import OpenAI
        from src.config import OPENAI_API_KEY
        client = OpenAI(api_key=OPENAI_API_KEY)
        client.models.list()
        lines.append("✅ OpenAI API reachable.")
    except Exception as e:
        lines.append(f"❌ OpenAI: {e}")

    await update.message.reply_text("\n".join(lines))


# ── /cost ─────────────────────────────────────────────────


async def cmd_cost(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_user.id):
        return
    try:
        from src.modules.db import get_connection, get_today_cost
        conn = get_connection()
        cost, count = get_today_cost(conn)
        conn.close()
        await update.message.reply_text(f"💰 Сегодня: ${cost:.4f} / {count} счетов")
    except Exception as e:
        await update.message.reply_text(f"💰 Ошибка: {e}")


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
    # Prevent concurrent runs
    if not _processing_lock.acquire(blocking=False):
        await query.edit_message_text("⏳ Обработка уже идёт. Подождите.")
        return

    try:
        msg = await query.edit_message_text("⏳ Запуск обработки...")

        from src.modules.pipeline import process_batch

        # Progress callback: update the same message
        progress_lines: list[str] = []

        def on_progress(done: int, total: int, line: str):
            progress_lines.append(line)
            # Keep last 10 lines
            visible = progress_lines[-10:]
            text = f"📄 Обработка: {done}/{total}\n\n" + "\n".join(visible)
            try:
                asyncio.get_event_loop().run_until_complete(
                    msg.edit_text(text)
                )
            except Exception:
                pass  # ignore edit conflicts

        result = await process_batch(progress_cb=None)  # TODO: wire progress_cb properly

        # Summary
        summary = (
            f"✅ Обработка завершена\n\n"
            f"✓ {result.success} успешно\n"
            f"⚠ {result.review} требует проверки\n"
            f"✗ {result.manual} в manual/\n"
            f"❌ {result.errors} ошибок\n\n"
            f"💰 Стоимость: ${result.total_cost:.4f}"
        )

        if result.cost_limit_hit:
            summary = "⚠️ Дневной лимит расходов достигнут. Попробуйте завтра."

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 Главное меню", callback_data="start_menu")]]
        )
        await msg.edit_text(summary, reply_markup=keyboard)

        # Send Excel file
        if result.excel_path and result.excel_path.exists():
            caption = f"✓ {result.success} | ⚠ {result.review} | ✗ {result.manual} | ${result.total_cost:.2f}"
            await ctx.bot.send_document(
                chat_id=query.message.chat_id,
                document=open(result.excel_path, "rb"),
                filename=result.excel_path.name,
                caption=caption,
            )

    except Exception as e:
        log.exception("Processing failed")
        await query.edit_message_text(f"❌ Ошибка обработки: {e}")
    finally:
        _processing_lock.release()


async def _handle_manual(query, ctx) -> None:
    from src.modules.file_manager import list_manual_files

    files = list_manual_files()
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
