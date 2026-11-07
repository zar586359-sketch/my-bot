import os

# Render Environment Variables များမှ အချက်အလက်များကို ယူမည်
API_ID = int(os.getenv("API_ID", "12345678"))
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
MODEL_NAME = "gemini-1.5-flash"

OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
