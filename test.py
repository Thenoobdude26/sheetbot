import os
from dotenv import load_dotenv  
from google import genai
from google.genai import types

load_dotenv()  # Load environment variables from .env file
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open("test_receipts/screenshot.png", "rb") as f:
    file_bytes = f.read()

receipt = types.Part.from_bytes(data=file_bytes, mime_type="image/png")

reponse = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[receipt, "What is on the receipt?"]
)
print(reponse.text)