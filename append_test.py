import os
import gspread
from dotenv import load_dotenv

load_dotenv()

gc = gspread.service_account(
    filename="service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
ws = gc.open_by_key(os.getenv("SHEET_ID")).worksheet("Expense Tracker")

row = ["2026-01-01", "TEST-001", "Test Vendor", "Other", "test row - delete me", 1.23, ""]
ws.append_row(row, value_input_option="USER_ENTERED")
print("Appended:", row)