import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from extract import extract
from sheet import append_expense

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED = {int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()}

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Save to sheet", callback_data="save"),
            InlineKeyboardButton("Cancel", callback_data="cancel"),
        ]
    ]
)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ALLOWED:
        print(f"Ignored message from user ID {user.id}")
        return

    msg = update.message
    if msg.document:
        tg_file = await msg.document.get_file()
        suffix = Path(msg.document.file_name or "").suffix.lower() or ".pdf"
    else:
        tg_file = await msg.photo[-1].get_file()
        suffix = ".jpg"

    await msg.reply_text("Reading receipt...")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"receipt{suffix}"
        await tg_file.download_to_drive(path)
        try:
            data = await asyncio.to_thread(extract, path)
        except Exception as e:
            await msg.reply_text(f"Couldn't read that file: {e}")
            return

    if all(v is None for v in data.values()):
        await msg.reply_text("That doesn't look like a receipt.")
        return

    context.user_data["pending"] = data

    lines = [f"{k}: {v}" for k, v in data.items()]
    if data.get("currency") and data["currency"] != "USD":
        lines.append(
            f"\n⚠️ Currency is {data['currency']}, but the sheet's Amount column is USD."
        )
    await msg.reply_text("\n".join(lines), reply_markup=BUTTONS)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ALLOWED:
        return

    pending = context.user_data.pop("pending", None)
    if pending is None:
        await query.edit_message_text(
            "Nothing pending (the bot may have restarted). Send the receipt again."
        )
        return

    if query.data == "save":
        try:
            await asyncio.to_thread(append_expense, pending)
        except Exception as e:
            context.user_data["pending"] = pending  # keep it so you can retry
            await query.edit_message_text(f"Couldn't save: {e}")
            return
        await query.edit_message_text("✅ Saved to the sheet.")
    else:
        await query.edit_message_text("Cancelled.")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.run_polling()


if __name__ == "__main__":
    main()