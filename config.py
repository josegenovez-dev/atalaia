import json
import os

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_URL = os.getenv(
    "SEATALK_BASE_URL",
    "https://openapi.seatalk.io",
)

GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "",
)

PLANILHAS_RAW = os.getenv(
    "PLANILHAS",
    "{}",
)

try:
    PLANILHAS = json.loads(PLANILHAS_RAW)
except json.JSONDecodeError as error:
    print(
        "ERRO AO LER PLANILHAS:",
        repr(error),
        flush=True,
    )
    PLANILHAS = {}
