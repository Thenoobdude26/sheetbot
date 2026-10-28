import os
import gspread
from dotenv import load_dotenv

load_dotenv()

gc = gspread.service_account(
    filename="service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
sh = gc.open_by_key(os.getenv("SHEET_ID"))

print("Tabs:", [ws.title for ws in sh.worksheets()])

ws = sh.worksheet("Expense Tracker")
for row in ws.get_all_values():
    print(row)