import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"
RULES = Path("rules.md").read_text()

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class Receipt(BaseModel):
    date: str | None = None
    invoice_number: str | None = None
    vendor: str | None = None
    category: Literal[
        "Hosting & Cloud",
        "Domain & Hosting",
        "Email",
        "Software",
        "Travel",
        "Food",
        "Office",
        "Other",
    ] | None = None
    amount: float | None = None
    currency: str | None = None


def extract(path):
    path = Path(path)
    mime = MIME_TYPES.get(path.suffix.lower())
    if mime is None:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    part = types.Part.from_bytes(data=path.read_bytes(), mime_type=mime)
    response = client.models.generate_content(
        model=MODEL,
        contents=[part, "Extract the receipt fields."],
        config=types.GenerateContentConfig(
            system_instruction=RULES,
            response_mime_type="application/json",
            response_schema=Receipt,
            temperature=0,
        ),
    )
    if response.parsed is not None:
        return response.parsed.model_dump()
    return json.loads(response.text)


if __name__ == "__main__":
    expected = json.loads(Path("expected.json").read_text())

    for p in sorted(Path("test_receipts").iterdir()):
        result = extract(p)
        want = expected.get(str(p)) or expected.get(p.name) or {}
        print(f"\n=== {p.name} ===")
        for field, got in result.items():
            if field not in want:
                print(f"  ?  {field}: {got!r} (not in expected.json)")
            elif got == want[field]:
                print(f"  OK {field}: {got!r}")
            else:
                print(f"  XX {field}: got {got!r}, expected {want[field]!r}")