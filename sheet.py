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


def append_expense(data, drive_link=""):
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
        drive_link,
    ]
    _ws.append_row([clean(v) for v in row], value_input_option="USER_ENTERED")


def _norm(value):
    return str(value or "").strip().lower()


def find_duplicate(data):
    """Return the sheet row number of a likely duplicate, or None."""
    rows = _ws.get_all_values()
    invoice = _norm(data.get("invoice_number"))
    vendor = _norm(data.get("vendor"))
    amount = data.get("amount")

    for number, row in enumerate(rows[1:], start=2):
        row = row + [""] * (7 - len(row))
        if invoice:
            if _norm(row[1]) == invoice:
                return number
        elif vendor and amount is not None:
            try:
                same_amount = abs(float(row[5].replace(",", "")) - amount) < 0.005
            except ValueError:
                continue
            if _norm(row[2]) == vendor and same_amount:
                return number
    return None