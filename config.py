import os

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_URL = os.getenv(
    "SEATALK_BASE_URL",
    "https://openapi.seatalk.io",
)
