import os

import gspread
from dotenv import load_dotenv

load_dotenv()

_gc = gspread.service_account(
    filename="service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
_ws = _gc.open_by_key(os.getenv("SHEET_ID")).worksheet("Expense Tracker")


def clean(value):
    if value is None:
        return ""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def append_expense(data):
    invoice = data.get("invoice_number")
    if invoice and invoice.isdigit() and invoice.startswith("0"):
        invoice = "'" + invoice

    row = [
        data.get("date"),
        invoice,
        data.get("vendor"),
        data.get("category"),
        data.get("description"),
        data.get("amount"),
        "",  # Drive Link, filled in later
    ]
    _ws.append_row([clean(v) for v in row], value_input_option="USER_ENTERED")