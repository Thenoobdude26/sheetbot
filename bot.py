import asyncio
import logging
import os
import re
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

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) 
log = logging.getLogger("sheetbot")

REQUIRED = [
    "TELEGRAM_BOT_TOKEN",
    "GEMINI_API_KEY",
    "ALLOWED_USER_IDS",
    "SHEET_ID",
    "DRIVE_FOLDER_ID",
]
missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

# These imports open the sheet when loaded, so they come after the check above
from drive import upload_receipt  # noqa: E402
from extract import MIME_TYPES, extract  # noqa: E402
from sheet import append_expense, find_duplicate  # noqa: E402

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED = {int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()}
MAX_BYTES = 20 * 1024 * 1024  # Telegram bots can't download files larger than this, devs please fix

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Save to sheet", callback_data="save"),
            InlineKeyboardButton("Cancel", callback_data="cancel"),
        ]
    ]
)


def safe_name(data, suffix):
    parts = [data.get("date"), data.get("vendor"), data.get("invoice_number")]
    name = "_".join(str(p) for p in parts if p)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "receipt"
    return name + suffix


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ALLOWED:
        log.warning("Ignored message from user ID %s", user.id)
        return

    msg = update.message
    if msg.document:
        media = msg.document
        suffix = Path(media.file_name or "").suffix.lower() or ".pdf"
        if suffix not in MIME_TYPES:
            await msg.reply_text("Please send a PDF, JPG, PNG or WEBP file.")
            return
        if media.file_size and media.file_size > MAX_BYTES:
            await msg.reply_text("That file is too big (the limit is 20 MB).")
            return
    else:
        media = msg.photo[-1]
        suffix = ".jpg"

    await msg.reply_text("Reading receipt...")

    try:
        tg_file = await media.get_file()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"receipt{suffix}"
            await tg_file.download_to_drive(path)
            file_bytes = path.read_bytes()
            data = await asyncio.to_thread(extract, path)
    except Exception:
        log.exception("Reading the receipt failed")
        await msg.reply_text(
            "Couldn't read that file. Please try again, or send a clearer copy."
        )
        return

    if all(v is None for v in data.values()):
        await msg.reply_text("That doesn't look like a receipt.")
        return

    context.user_data["pending"] = {
        "data": data,
        "file_bytes": file_bytes,
        "suffix": suffix,
        "link": None,
        "saving": False,
    }

    lines = [f"{k}: {v}" for k, v in data.items()]
    if data.get("currency") and data["currency"] != "USD":
        lines.append(
            f"\n⚠️ Currency is {data['currency']}, but the sheet's Amount column is USD."
        )
    try:
        dup_row = await asyncio.to_thread(find_duplicate, data)
    except Exception:
        log.exception("Duplicate check failed")
        dup_row = None
        lines.append("\n(Couldn't check for duplicates.)")
    if dup_row:
        lines.append(f"\n⚠️ Possible duplicate of row {dup_row} in the sheet.")

    await msg.reply_text("\n".join(lines), reply_markup=BUTTONS)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ALLOWED:
        return

    pending = context.user_data.get("pending")
    if pending is None:
        await query.edit_message_text(
            "Nothing pending (the bot may have restarted). Send the receipt again."
        )
        return

    original = query.message.text if query.message and query.message.text else ""

    if query.data == "cancel":
        context.user_data.pop("pending", None)
        await query.edit_message_text(f"{original}\n\nCancelled.")
        return

    if pending["saving"]:
        return  # AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHhhh
    pending["saving"] = True

    try:
        if pending["link"] is None:
            filename = safe_name(pending["data"], pending["suffix"])
            mime = MIME_TYPES.get(pending["suffix"], "application/octet-stream")
            pending["link"] = await asyncio.to_thread(
                upload_receipt, pending["file_bytes"], filename, mime
            )
        await asyncio.to_thread(append_expense, pending["data"], pending["link"])
    except Exception:
        log.exception("Saving failed")
        pending["saving"] = False
        await query.edit_message_text(
            f"{original}\n\n❌ Couldn't save. Press Save to retry.",
            reply_markup=BUTTONS,
        )
        return

    context.user_data.pop("pending", None)
    await query.edit_message_text(f"{original}\n\n✅ Saved to the sheet.")


async def on_error(update, context):
    log.error("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something went wrong (network?). Please send the receipt again."
            )
        except Exception:
            pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ALLOWED:
        await update.message.reply_text("I'm alive. Send me a receipt as a PDF or photo.")

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_error_handler(on_error)
    log.info("Bot started")
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.run_polling(bootstrap_retries=-1)



if __name__ == "__main__":
    main()